# Smart Context Manager - ITEM 125
# AI memory system that tracks and manages project context for intelligent assistance

from typing import List, Dict, Optional, Any, Set
from datetime import datetime, timedelta
from dataclasses import dataclass, field
from enum import Enum
import json
from collections import defaultdict

from ..core.logging_config import get_logger
from ..core.database_enhanced import get_db
from sqlalchemy import text

logger = get_logger(__name__)


class ContextType(str, Enum):
    """Types of context information."""
    PROJECT = "project"
    DOCUMENT = "document"
    BIM_MODEL = "bim_model"
    CONVERSATION = "conversation"
    TASK = "task"
    USER_PREFERENCE = "user_preference"
    DECISION = "decision"
    ISSUE = "issue"


class ContextPriority(str, Enum):
    """Priority levels for context."""
    CRITICAL = "critical"  # Always keep in context
    HIGH = "high"          # Keep if space available
    MEDIUM = "medium"      # Keep for recent activity
    LOW = "low"            # Can be evicted easily


@dataclass
class ContextItem:
    """Individual piece of context."""
    id: str
    type: ContextType
    priority: ContextPriority
    content: Dict[str, Any]
    metadata: Dict[str, Any] = field(default_factory=dict)
    created_at: datetime = field(default_factory=datetime.utcnow)
    accessed_at: datetime = field(default_factory=datetime.utcnow)
    access_count: int = 0
    tags: Set[str] = field(default_factory=set)

    def mark_accessed(self):
        """Update access tracking."""
        self.accessed_at = datetime.utcnow()
        self.access_count += 1

    @property
    def age_hours(self) -> float:
        """Age of context item in hours."""
        return (datetime.utcnow() - self.created_at).total_seconds() / 3600

    @property
    def recency_score(self) -> float:
        """Calculate recency score (0-1, higher is more recent)."""
        hours = self.age_hours
        # Decay function: score halves every 24 hours
        return 0.5 ** (hours / 24)

    @property
    def importance_score(self) -> float:
        """Calculate importance score based on priority and usage."""
        priority_scores = {
            ContextPriority.CRITICAL: 1.0,
            ContextPriority.HIGH: 0.75,
            ContextPriority.MEDIUM: 0.5,
            ContextPriority.LOW: 0.25,
        }

        base_score = priority_scores.get(self.priority, 0.5)

        # Boost score based on access frequency
        access_boost = min(0.3, self.access_count * 0.05)

        return min(1.0, base_score + access_boost)

    @property
    def retention_score(self) -> float:
        """Combined score for retention decisions."""
        # Weight: 60% importance, 40% recency
        return (self.importance_score * 0.6) + (self.recency_score * 0.4)


class SmartContextManager:
    """
    Manages AI context window with intelligent prioritization.

    Features:
    - Dynamic context loading based on relevance
    - Automatic eviction when capacity reached
    - Multi-tenancy support (project-scoped)
    - Context summarization for compression
    - Usage tracking and analytics
    """

    def __init__(
        self,
        max_capacity_kb: int = 100,  # 100KB context window
        project_id: Optional[str] = None
    ):
        """
        Initialize Smart Context Manager.

        Args:
            max_capacity_kb: Maximum context size in kilobytes
            project_id: Optional project scope
        """
        self.max_capacity_kb = max_capacity_kb
        self.project_id = project_id
        self.context: Dict[str, ContextItem] = {}
        self.logger = get_logger(self.__class__.__name__)

    @property
    def current_capacity_kb(self) -> float:
        """Calculate current context size in KB."""
        total_size = sum(
            len(json.dumps(item.content)) + len(json.dumps(item.metadata))
            for item in self.context.values()
        )
        return total_size / 1024

    @property
    def capacity_percent(self) -> float:
        """Get current capacity usage as percentage."""
        return (self.current_capacity_kb / self.max_capacity_kb) * 100

    @property
    def available_capacity_kb(self) -> float:
        """Get available capacity in KB."""
        return max(0, self.max_capacity_kb - self.current_capacity_kb)

    def add_context(
        self,
        item_id: str,
        context_type: ContextType,
        content: Dict[str, Any],
        priority: ContextPriority = ContextPriority.MEDIUM,
        metadata: Optional[Dict[str, Any]] = None,
        tags: Optional[Set[str]] = None
    ) -> bool:
        """
        Add context item to the manager.

        Args:
            item_id: Unique identifier
            context_type: Type of context
            content: Context content
            priority: Priority level
            metadata: Optional metadata
            tags: Optional tags for filtering

        Returns:
            True if added successfully, False if capacity exceeded
        """
        item = ContextItem(
            id=item_id,
            type=context_type,
            priority=priority,
            content=content,
            metadata=metadata or {},
            tags=tags or set()
        )

        # Calculate size
        item_size_kb = (
            len(json.dumps(content)) + len(json.dumps(metadata or {}))
        ) / 1024

        # Check if we need to make room
        while (self.current_capacity_kb + item_size_kb) > self.max_capacity_kb:
            if not self._evict_lowest_priority():
                self.logger.warning(f"Cannot add context {item_id}: capacity exceeded")
                return False

        self.context[item_id] = item
        self.logger.info(
            f"Added context {item_id} ({context_type.value}) - "
            f"Capacity: {self.capacity_percent:.1f}%"
        )
        return True

    def get_context(self, item_id: str) -> Optional[ContextItem]:
        """
        Retrieve context item and mark as accessed.

        Args:
            item_id: Context item ID

        Returns:
            Context item if found, None otherwise
        """
        item = self.context.get(item_id)
        if item:
            item.mark_accessed()
        return item

    def remove_context(self, item_id: str) -> bool:
        """
        Remove context item.

        Args:
            item_id: Context item ID

        Returns:
            True if removed, False if not found
        """
        if item_id in self.context:
            del self.context[item_id]
            self.logger.info(f"Removed context {item_id}")
            return True
        return False

    def _evict_lowest_priority(self) -> bool:
        """
        Evict the lowest priority context item.

        Returns:
            True if item was evicted, False if no items to evict
        """
        # Never evict CRITICAL items
        evictable = {
            item_id: item for item_id, item in self.context.items()
            if item.priority != ContextPriority.CRITICAL
        }

        if not evictable:
            return False

        # Find item with lowest retention score
        lowest_item_id = min(
            evictable.keys(),
            key=lambda k: evictable[k].retention_score
        )

        self.logger.info(
            f"Evicting context {lowest_item_id} "
            f"(score: {evictable[lowest_item_id].retention_score:.2f})"
        )
        del self.context[lowest_item_id]
        return True

    def search_context(
        self,
        query: str,
        context_types: Optional[List[ContextType]] = None,
        tags: Optional[Set[str]] = None,
        limit: int = 10
    ) -> List[ContextItem]:
        """
        Search context items.

        Args:
            query: Search query
            context_types: Filter by context types
            tags: Filter by tags
            limit: Maximum results

        Returns:
            List of matching context items
        """
        results = []
        query_lower = query.lower()

        for item in self.context.values():
            # Filter by type
            if context_types and item.type not in context_types:
                continue

            # Filter by tags
            if tags and not tags.intersection(item.tags):
                continue

            # Search in content and metadata
            content_str = json.dumps(item.content).lower()
            metadata_str = json.dumps(item.metadata).lower()

            if query_lower in content_str or query_lower in metadata_str:
                item.mark_accessed()
                results.append(item)

        # Sort by retention score (relevance)
        results.sort(key=lambda x: x.retention_score, reverse=True)
        return results[:limit]

    def get_summary(self) -> Dict[str, Any]:
        """
        Get context manager summary statistics.

        Returns:
            Summary dictionary
        """
        type_counts = defaultdict(int)
        priority_counts = defaultdict(int)

        for item in self.context.values():
            type_counts[item.type.value] += 1
            priority_counts[item.priority.value] += 1

        return {
            "total_items": len(self.context),
            "capacity_kb": self.current_capacity_kb,
            "max_capacity_kb": self.max_capacity_kb,
            "capacity_percent": self.capacity_percent,
            "available_kb": self.available_capacity_kb,
            "items_by_type": dict(type_counts),
            "items_by_priority": dict(priority_counts),
            "project_id": self.project_id,
        }

    def compress_context(self, target_percent: float = 80.0) -> int:
        """
        Compress context to target capacity percentage.

        Args:
            target_percent: Target capacity percentage

        Returns:
            Number of items evicted
        """
        evicted_count = 0
        target_kb = self.max_capacity_kb * (target_percent / 100)

        while self.current_capacity_kb > target_kb:
            if not self._evict_lowest_priority():
                break
            evicted_count += 1

        self.logger.info(
            f"Compressed context: evicted {evicted_count} items, "
            f"now at {self.capacity_percent:.1f}%"
        )
        return evicted_count

    def refresh_stale_items(self, max_age_hours: float = 72.0):
        """
        Remove items older than specified age (except CRITICAL).

        Args:
            max_age_hours: Maximum age in hours
        """
        stale_items = [
            item_id for item_id, item in self.context.items()
            if item.age_hours > max_age_hours and item.priority != ContextPriority.CRITICAL
        ]

        for item_id in stale_items:
            del self.context[item_id]

        self.logger.info(f"Removed {len(stale_items)} stale context items")

    def load_project_context(self, project_id: str, db = None) -> int:
        """
        Load essential project context from database.

        Args:
            project_id: Project ID to load context for
            db: Database session

        Returns:
            Number of context items loaded
        """
        loaded_count = 0

        try:
            # Load project metadata
            self.add_context(
                f"project:{project_id}",
                ContextType.PROJECT,
                {"project_id": project_id, "loaded_at": datetime.utcnow().isoformat()},
                priority=ContextPriority.CRITICAL,
                tags={"project", "metadata"}
            )
            loaded_count += 1

            # In production, load recent documents, tasks, decisions, etc.
            self.logger.info(f"Loaded {loaded_count} project context items")

        except Exception as e:
            self.logger.error(f"Failed to load project context: {e}")

        return loaded_count

    def export_context(self) -> Dict[str, Any]:
        """
        Export full context state for persistence.

        Returns:
            Serializable context state
        """
        return {
            "project_id": self.project_id,
            "max_capacity_kb": self.max_capacity_kb,
            "items": [
                {
                    "id": item.id,
                    "type": item.type.value,
                    "priority": item.priority.value,
                    "content": item.content,
                    "metadata": item.metadata,
                    "created_at": item.created_at.isoformat(),
                    "accessed_at": item.accessed_at.isoformat(),
                    "access_count": item.access_count,
                    "tags": list(item.tags),
                }
                for item in self.context.values()
            ],
            "summary": self.get_summary(),
        }


# Global context managers (one per project)
_context_managers: Dict[str, SmartContextManager] = {}


def get_smart_context(
    project_id: Optional[str] = None,
    max_capacity_kb: int = 100
) -> SmartContextManager:
    """
    Get or create smart context manager for a project.

    Args:
        project_id: Project ID (None for global context)
        max_capacity_kb: Maximum capacity

    Returns:
        Smart context manager instance
    """
    key = project_id or "global"

    if key not in _context_managers:
        _context_managers[key] = SmartContextManager(
            max_capacity_kb=max_capacity_kb,
            project_id=project_id
        )

    return _context_managers[key]
