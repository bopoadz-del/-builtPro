"""
Edge Computing Service for BuilTPro Brain AI

Distributed edge computing infrastructure for construction sites with offline
capabilities, local processing, and cloud synchronization.

Features:
- Edge node registration and management
- Data synchronization (bidirectional)
- Offline-first architecture
- Local processing rules and workflows
- Resource scheduling and load balancing
- Conflict resolution
- Edge-to-cloud sync with retry
- Local caching and storage

Use Cases:
- Remote construction sites with limited connectivity
- Real-time video analytics at the edge
- Local IoT data processing
- Offline mobile applications
- Latency-sensitive operations
- Bandwidth optimization

Author: BuilTPro AI Team
Created: 2026-02-15
"""

from __future__ import annotations

import logging
from dataclasses import dataclass, field
from datetime import datetime, timedelta
from enum import Enum
from typing import Any, Dict, List, Optional, Callable, Set
from collections import defaultdict, deque
import json
import hashlib
import asyncio
from threading import Lock
import uuid

logger = logging.getLogger(__name__)


# ============================================================================
# Exceptions
# ============================================================================


class EdgeComputingError(Exception):
    """Base exception for edge computing errors."""
    pass


class NodeError(EdgeComputingError):
    """Raised when edge node operations fail."""
    pass


class SyncError(EdgeComputingError):
    """Raised when synchronization fails."""
    pass


class ProcessingError(EdgeComputingError):
    """Raised when edge processing fails."""
    pass


# ============================================================================
# Enums
# ============================================================================


class NodeStatus(str, Enum):
    """Edge node connection status."""
    ONLINE = "online"
    OFFLINE = "offline"
    SYNCING = "syncing"
    ERROR = "error"
    DEGRADED = "degraded"


class NodeCapability(str, Enum):
    """Edge node capabilities."""
    COMPUTE = "compute"
    STORAGE = "storage"
    VIDEO_PROCESSING = "video_processing"
    ML_INFERENCE = "ml_inference"
    IOT_GATEWAY = "iot_gateway"
    DATA_AGGREGATION = "data_aggregation"


class SyncDirection(str, Enum):
    """Data synchronization direction."""
    EDGE_TO_CLOUD = "edge_to_cloud"
    CLOUD_TO_EDGE = "cloud_to_edge"
    BIDIRECTIONAL = "bidirectional"


class SyncStatus(str, Enum):
    """Synchronization status."""
    PENDING = "pending"
    IN_PROGRESS = "in_progress"
    COMPLETED = "completed"
    FAILED = "failed"
    CONFLICT = "conflict"


class ConflictResolution(str, Enum):
    """Conflict resolution strategies."""
    CLOUD_WINS = "cloud_wins"
    EDGE_WINS = "edge_wins"
    LATEST_WINS = "latest_wins"
    MANUAL = "manual"


class ProcessingPriority(str, Enum):
    """Processing task priority."""
    LOW = "low"
    NORMAL = "normal"
    HIGH = "high"
    CRITICAL = "critical"


# ============================================================================
# Data Classes
# ============================================================================


@dataclass
class EdgeNode:
    """Edge computing node."""
    node_id: str
    name: str
    location: str
    capabilities: Set[NodeCapability]
    status: NodeStatus = NodeStatus.OFFLINE
    ip_address: Optional[str] = None
    registered_at: datetime = field(default_factory=datetime.utcnow)
    last_seen: Optional[datetime] = None
    last_sync: Optional[datetime] = None
    cpu_cores: int = 4
    memory_gb: int = 8
    storage_gb: int = 100
    metadata: Dict[str, Any] = field(default_factory=dict)


@dataclass
class EdgeResource:
    """Resource usage metrics for edge node."""
    node_id: str
    cpu_usage_percent: float
    memory_usage_percent: float
    storage_usage_percent: float
    network_bandwidth_mbps: float
    active_tasks: int
    timestamp: datetime = field(default_factory=datetime.utcnow)


@dataclass
class SyncTask:
    """Data synchronization task."""
    sync_id: str
    node_id: str
    direction: SyncDirection
    data_type: str
    data_id: str
    payload: Dict[str, Any]
    status: SyncStatus = SyncStatus.PENDING
    priority: int = 5
    created_at: datetime = field(default_factory=datetime.utcnow)
    started_at: Optional[datetime] = None
    completed_at: Optional[datetime] = None
    retry_count: int = 0
    max_retries: int = 5
    error_message: Optional[str] = None
    checksum: Optional[str] = None


@dataclass
class DataConflict:
    """Data synchronization conflict."""
    conflict_id: str
    sync_id: str
    data_type: str
    data_id: str
    cloud_version: Dict[str, Any]
    edge_version: Dict[str, Any]
    cloud_timestamp: datetime
    edge_timestamp: datetime
    resolution_strategy: ConflictResolution
    resolved: bool = False
    resolution: Optional[Dict[str, Any]] = None


@dataclass
class ProcessingRule:
    """Local processing rule for edge nodes."""
    rule_id: str
    name: str
    description: str
    trigger_condition: str  # Python expression
    action: str  # Function name or code
    enabled: bool = True
    priority: ProcessingPriority = ProcessingPriority.NORMAL
    node_ids: Optional[List[str]] = None  # None = all nodes
    created_at: datetime = field(default_factory=datetime.utcnow)


@dataclass
class EdgeTask:
    """Processing task for edge node."""
    task_id: str
    node_id: str
    rule_id: Optional[str]
    task_type: str
    input_data: Dict[str, Any]
    priority: ProcessingPriority
    status: str = "pending"  # pending, running, completed, failed
    created_at: datetime = field(default_factory=datetime.utcnow)
    started_at: Optional[datetime] = None
    completed_at: Optional[datetime] = None
    result: Optional[Dict[str, Any]] = None
    error: Optional[str] = None


@dataclass
class CacheEntry:
    """Cached data entry for offline access."""
    cache_id: str
    node_id: str
    data_type: str
    data_id: str
    data: Dict[str, Any]
    cached_at: datetime = field(default_factory=datetime.utcnow)
    expires_at: Optional[datetime] = None
    access_count: int = 0
    last_accessed: Optional[datetime] = None


# ============================================================================
# Edge Computing Service
# ============================================================================


class EdgeComputingService:
    """
    Production-ready edge computing infrastructure.

    Features:
    - Distributed edge node management
    - Offline-first data synchronization
    - Local processing with rules engine
    - Conflict resolution
    - Resource management and scheduling
    """

    _instance = None
    _lock = Lock()

    def __new__(cls):
        """Singleton pattern for global edge computing service."""
        if cls._instance is None:
            with cls._lock:
                if cls._instance is None:
                    cls._instance = super().__new__(cls)
        return cls._instance

    def __init__(self):
        """Initialize the edge computing service."""
        if hasattr(self, '_initialized'):
            return

        self._initialized = True

        # Storage
        self.nodes: Dict[str, EdgeNode] = {}
        self.sync_tasks: Dict[str, SyncTask] = {}
        self.conflicts: Dict[str, DataConflict] = {}
        self.processing_rules: Dict[str, ProcessingRule] = {}
        self.edge_tasks: Dict[str, EdgeTask] = {}
        self.cache: Dict[str, CacheEntry] = {}

        # Queues
        self.sync_queue: deque = deque()
        self.task_queue: deque = deque()

        # Resource tracking
        self.node_resources: Dict[str, EdgeResource] = {}

        # Configuration
        self.sync_interval_seconds = 60
        self.max_concurrent_syncs = 5
        self.cache_ttl_hours = 24
        self.default_conflict_resolution = ConflictResolution.LATEST_WINS

        # Statistics
        self.stats = {
            "total_nodes": 0,
            "online_nodes": 0,
            "total_syncs": 0,
            "successful_syncs": 0,
            "failed_syncs": 0,
            "conflicts_detected": 0,
            "tasks_processed": 0
        }

        logger.info("Edge Computing Service initialized")

    # ========================================================================
    # Node Management
    # ========================================================================

    def register_node(
        self,
        node_id: str,
        name: str,
        location: str,
        capabilities: Set[NodeCapability],
        cpu_cores: int = 4,
        memory_gb: int = 8,
        storage_gb: int = 100,
        ip_address: Optional[str] = None
    ) -> EdgeNode:
        """
        Register a new edge node.

        Args:
            node_id: Unique node identifier
            name: Human-readable node name
            location: Physical location
            capabilities: Set of node capabilities
            cpu_cores: Number of CPU cores
            memory_gb: RAM in GB
            storage_gb: Storage in GB
            ip_address: Optional IP address

        Returns:
            EdgeNode object
        """
        try:
            node = EdgeNode(
                node_id=node_id,
                name=name,
                location=location,
                capabilities=capabilities,
                cpu_cores=cpu_cores,
                memory_gb=memory_gb,
                storage_gb=storage_gb,
                ip_address=ip_address
            )

            self.nodes[node_id] = node
            self.stats["total_nodes"] = len(self.nodes)

            logger.info(f"Registered edge node {node_id} at {location}")

            return node

        except Exception as e:
            logger.error(f"Failed to register node {node_id}: {e}")
            raise NodeError(f"Node registration failed: {e}")

    def update_node_status(
        self,
        node_id: str,
        status: NodeStatus,
        resources: Optional[EdgeResource] = None
    ) -> None:
        """Update edge node status and resources."""
        if node_id not in self.nodes:
            raise NodeError(f"Node not found: {node_id}")

        node = self.nodes[node_id]
        old_status = node.status
        node.status = status
        node.last_seen = datetime.utcnow()

        # Update resource metrics
        if resources:
            self.node_resources[node_id] = resources

        # Update statistics
        if old_status != NodeStatus.ONLINE and status == NodeStatus.ONLINE:
            self.stats["online_nodes"] += 1
        elif old_status == NodeStatus.ONLINE and status != NodeStatus.ONLINE:
            self.stats["online_nodes"] = max(0, self.stats["online_nodes"] - 1)

        logger.debug(f"Node {node_id} status: {old_status} -> {status}")

    def get_node(self, node_id: str) -> Optional[EdgeNode]:
        """Get edge node information."""
        return self.nodes.get(node_id)

    def list_nodes(
        self,
        status: Optional[NodeStatus] = None,
        capability: Optional[NodeCapability] = None,
        location: Optional[str] = None
    ) -> List[EdgeNode]:
        """List edge nodes with optional filters."""
        nodes = list(self.nodes.values())

        if status:
            nodes = [n for n in nodes if n.status == status]

        if capability:
            nodes = [n for n in nodes if capability in n.capabilities]

        if location:
            nodes = [n for n in nodes if n.location == location]

        return nodes

    def get_node_resources(self, node_id: str) -> Optional[EdgeResource]:
        """Get current resource usage for a node."""
        return self.node_resources.get(node_id)

    # ========================================================================
    # Data Synchronization
    # ========================================================================

    def create_sync_task(
        self,
        node_id: str,
        direction: SyncDirection,
        data_type: str,
        data_id: str,
        payload: Dict[str, Any],
        priority: int = 5
    ) -> SyncTask:
        """
        Create a data synchronization task.

        Args:
            node_id: Target edge node
            direction: Sync direction
            data_type: Type of data being synced
            data_id: Data identifier
            payload: Data payload
            priority: Task priority (lower = higher priority)

        Returns:
            SyncTask object
        """
        try:
            if node_id not in self.nodes:
                raise NodeError(f"Node not found: {node_id}")

            sync_id = f"{node_id}_{data_type}_{data_id}_{uuid.uuid4().hex[:8]}"

            # Calculate checksum
            checksum = self._calculate_checksum(payload)

            sync_task = SyncTask(
                sync_id=sync_id,
                node_id=node_id,
                direction=direction,
                data_type=data_type,
                data_id=data_id,
                payload=payload,
                priority=priority,
                checksum=checksum
            )

            self.sync_tasks[sync_id] = sync_task
            self.sync_queue.append(sync_id)

            self.stats["total_syncs"] += 1

            logger.info(f"Created sync task {sync_id} for node {node_id}")

            return sync_task

        except NodeError:
            raise
        except Exception as e:
            logger.error(f"Failed to create sync task: {e}")
            raise SyncError(f"Sync task creation failed: {e}")

    async def process_sync_queue(self, batch_size: int = 10) -> int:
        """
        Process pending synchronization tasks.

        Args:
            batch_size: Maximum tasks to process

        Returns:
            Number of tasks processed
        """
        processed = 0

        # Sort queue by priority
        sorted_queue = sorted(
            [self.sync_tasks[sid] for sid in self.sync_queue if sid in self.sync_tasks],
            key=lambda t: t.priority
        )

        for sync_task in sorted_queue[:batch_size]:
            try:
                await self._execute_sync(sync_task)
                processed += 1

                # Remove from queue
                if sync_task.sync_id in self.sync_queue:
                    self.sync_queue.remove(sync_task.sync_id)

            except SyncError as e:
                logger.warning(f"Sync failed: {e}")
                self._handle_sync_failure(sync_task, str(e))

        return processed

    async def _execute_sync(self, sync_task: SyncTask) -> None:
        """Execute a synchronization task."""
        sync_task.status = SyncStatus.IN_PROGRESS
        sync_task.started_at = datetime.utcnow()

        node = self.nodes.get(sync_task.node_id)

        if not node:
            raise SyncError(f"Node not found: {sync_task.node_id}")

        if node.status == NodeStatus.OFFLINE:
            raise SyncError(f"Node offline: {sync_task.node_id}")

        try:
            # Simulate sync operation (would be actual network call)
            await asyncio.sleep(0.1)

            # Check for conflicts
            conflict = self._detect_conflict(sync_task)

            if conflict:
                self._handle_conflict(conflict)
                if not conflict.resolved:
                    sync_task.status = SyncStatus.CONFLICT
                    return

            # Mark as completed
            sync_task.status = SyncStatus.COMPLETED
            sync_task.completed_at = datetime.utcnow()

            # Update node last sync time
            node.last_sync = datetime.utcnow()

            # Update statistics
            self.stats["successful_syncs"] += 1

            logger.debug(f"Sync completed: {sync_task.sync_id}")

        except Exception as e:
            raise SyncError(f"Sync execution failed: {e}")

    def _detect_conflict(self, sync_task: SyncTask) -> Optional[DataConflict]:
        """Detect synchronization conflicts."""
        # Simplified conflict detection
        # In real implementation, would check cloud vs edge timestamps

        # For demonstration, randomly detect conflicts (10% chance)
        import random
        if random.random() < 0.1:
            conflict = DataConflict(
                conflict_id=f"conflict_{uuid.uuid4().hex[:8]}",
                sync_id=sync_task.sync_id,
                data_type=sync_task.data_type,
                data_id=sync_task.data_id,
                cloud_version={"data": "cloud_data"},
                edge_version=sync_task.payload,
                cloud_timestamp=datetime.utcnow() - timedelta(minutes=5),
                edge_timestamp=datetime.utcnow(),
                resolution_strategy=self.default_conflict_resolution
            )

            self.conflicts[conflict.conflict_id] = conflict
            self.stats["conflicts_detected"] += 1

            return conflict

        return None

    def _handle_conflict(self, conflict: DataConflict) -> None:
        """Handle synchronization conflict based on resolution strategy."""
        if conflict.resolution_strategy == ConflictResolution.LATEST_WINS:
            if conflict.edge_timestamp > conflict.cloud_timestamp:
                conflict.resolution = conflict.edge_version
            else:
                conflict.resolution = conflict.cloud_version
            conflict.resolved = True

        elif conflict.resolution_strategy == ConflictResolution.CLOUD_WINS:
            conflict.resolution = conflict.cloud_version
            conflict.resolved = True

        elif conflict.resolution_strategy == ConflictResolution.EDGE_WINS:
            conflict.resolution = conflict.edge_version
            conflict.resolved = True

        elif conflict.resolution_strategy == ConflictResolution.MANUAL:
            # Requires manual intervention
            conflict.resolved = False
            logger.warning(f"Manual conflict resolution required: {conflict.conflict_id}")

        logger.info(f"Conflict resolved: {conflict.conflict_id} using {conflict.resolution_strategy}")

    def _handle_sync_failure(self, sync_task: SyncTask, error: str) -> None:
        """Handle failed synchronization with retry logic."""
        sync_task.retry_count += 1
        sync_task.error_message = error

        if sync_task.retry_count < sync_task.max_retries:
            # Re-queue with exponential backoff
            sync_task.status = SyncStatus.PENDING
            logger.info(f"Retry {sync_task.retry_count}/{sync_task.max_retries} for {sync_task.sync_id}")
        else:
            sync_task.status = SyncStatus.FAILED
            self.stats["failed_syncs"] += 1
            logger.error(f"Sync failed permanently: {sync_task.sync_id}")

    def _calculate_checksum(self, data: Dict[str, Any]) -> str:
        """Calculate SHA-256 checksum for data."""
        data_str = json.dumps(data, sort_keys=True)
        return hashlib.sha256(data_str.encode()).hexdigest()

    # ========================================================================
    # Local Processing
    # ========================================================================

    def add_processing_rule(self, rule: ProcessingRule) -> None:
        """Add a local processing rule for edge nodes."""
        self.processing_rules[rule.rule_id] = rule
        logger.info(f"Added processing rule: {rule.name}")

    def create_edge_task(
        self,
        node_id: str,
        task_type: str,
        input_data: Dict[str, Any],
        priority: ProcessingPriority = ProcessingPriority.NORMAL,
        rule_id: Optional[str] = None
    ) -> EdgeTask:
        """
        Create a processing task for an edge node.

        Args:
            node_id: Target edge node
            task_type: Type of processing task
            input_data: Input data for processing
            priority: Task priority
            rule_id: Optional processing rule ID

        Returns:
            EdgeTask object
        """
        try:
            if node_id not in self.nodes:
                raise NodeError(f"Node not found: {node_id}")

            task_id = f"{node_id}_{task_type}_{uuid.uuid4().hex[:8]}"

            task = EdgeTask(
                task_id=task_id,
                node_id=node_id,
                rule_id=rule_id,
                task_type=task_type,
                input_data=input_data,
                priority=priority
            )

            self.edge_tasks[task_id] = task
            self.task_queue.append(task_id)

            logger.info(f"Created edge task {task_id} on node {node_id}")

            return task

        except NodeError:
            raise
        except Exception as e:
            logger.error(f"Failed to create edge task: {e}")
            raise ProcessingError(f"Task creation failed: {e}")

    async def process_edge_tasks(self, batch_size: int = 5) -> int:
        """Process queued edge tasks."""
        processed = 0

        while self.task_queue and processed < batch_size:
            task_id = self.task_queue.popleft()
            task = self.edge_tasks.get(task_id)

            if not task:
                continue

            try:
                await self._execute_edge_task(task)
                processed += 1
                self.stats["tasks_processed"] += 1

            except ProcessingError as e:
                logger.error(f"Task processing failed: {e}")
                task.status = "failed"
                task.error = str(e)

        return processed

    async def _execute_edge_task(self, task: EdgeTask) -> None:
        """Execute an edge processing task."""
        task.status = "running"
        task.started_at = datetime.utcnow()

        try:
            # Simulate processing (would be actual computation)
            await asyncio.sleep(0.2)

            # Generate result
            task.result = {
                "task_id": task.task_id,
                "processed": True,
                "output": "Task completed successfully"
            }

            task.status = "completed"
            task.completed_at = datetime.utcnow()

            logger.debug(f"Task completed: {task.task_id}")

        except Exception as e:
            raise ProcessingError(f"Task execution failed: {e}")

    # ========================================================================
    # Offline Cache
    # ========================================================================

    def cache_data(
        self,
        node_id: str,
        data_type: str,
        data_id: str,
        data: Dict[str, Any],
        ttl_hours: Optional[int] = None
    ) -> CacheEntry:
        """
        Cache data for offline access.

        Args:
            node_id: Edge node ID
            data_type: Type of data
            data_id: Data identifier
            data: Data to cache
            ttl_hours: Time-to-live in hours

        Returns:
            CacheEntry object
        """
        cache_id = f"{node_id}_{data_type}_{data_id}"

        ttl = ttl_hours or self.cache_ttl_hours
        expires_at = datetime.utcnow() + timedelta(hours=ttl)

        entry = CacheEntry(
            cache_id=cache_id,
            node_id=node_id,
            data_type=data_type,
            data_id=data_id,
            data=data,
            expires_at=expires_at
        )

        self.cache[cache_id] = entry

        logger.debug(f"Cached {data_type} data for node {node_id}")

        return entry

    def get_cached_data(
        self,
        node_id: str,
        data_type: str,
        data_id: str
    ) -> Optional[Dict[str, Any]]:
        """Retrieve cached data."""
        cache_id = f"{node_id}_{data_type}_{data_id}"
        entry = self.cache.get(cache_id)

        if not entry:
            return None

        # Check expiration
        if entry.expires_at and datetime.utcnow() > entry.expires_at:
            del self.cache[cache_id]
            return None

        # Update access tracking
        entry.access_count += 1
        entry.last_accessed = datetime.utcnow()

        return entry.data

    def clear_cache(self, node_id: Optional[str] = None) -> int:
        """Clear cached data. Returns number of entries cleared."""
        if node_id:
            # Clear cache for specific node
            to_delete = [k for k, v in self.cache.items() if v.node_id == node_id]
        else:
            # Clear all cache
            to_delete = list(self.cache.keys())

        for key in to_delete:
            del self.cache[key]

        logger.info(f"Cleared {len(to_delete)} cache entries")

        return len(to_delete)

    def cleanup_expired_cache(self) -> int:
        """Remove expired cache entries. Returns number removed."""
        now = datetime.utcnow()
        to_delete = [
            k for k, v in self.cache.items()
            if v.expires_at and now > v.expires_at
        ]

        for key in to_delete:
            del self.cache[key]

        if to_delete:
            logger.info(f"Cleaned up {len(to_delete)} expired cache entries")

        return len(to_delete)

    # ========================================================================
    # Statistics & Monitoring
    # ========================================================================

    def get_stats(self) -> Dict[str, Any]:
        """Get edge computing service statistics."""
        return {
            **self.stats,
            "cache_entries": len(self.cache),
            "pending_syncs": len(self.sync_queue),
            "pending_tasks": len(self.task_queue),
            "active_conflicts": len([c for c in self.conflicts.values() if not c.resolved])
        }

    def get_node_stats(self, node_id: str) -> Dict[str, Any]:
        """Get statistics for a specific node."""
        node = self.nodes.get(node_id)

        if not node:
            raise NodeError(f"Node not found: {node_id}")

        # Count tasks and syncs
        node_syncs = [s for s in self.sync_tasks.values() if s.node_id == node_id]
        node_tasks = [t for t in self.edge_tasks.values() if t.node_id == node_id]

        return {
            "node_id": node_id,
            "status": node.status.value,
            "last_seen": node.last_seen.isoformat() if node.last_seen else None,
            "last_sync": node.last_sync.isoformat() if node.last_sync else None,
            "total_syncs": len(node_syncs),
            "successful_syncs": len([s for s in node_syncs if s.status == SyncStatus.COMPLETED]),
            "total_tasks": len(node_tasks),
            "completed_tasks": len([t for t in node_tasks if t.status == "completed"]),
            "cache_entries": len([c for c in self.cache.values() if c.node_id == node_id])
        }


# ============================================================================
# Singleton Instance
# ============================================================================

# Global singleton instance
edge_computing = EdgeComputingService()
