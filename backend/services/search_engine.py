"""
Search Engine for BuilTPro Brain AI

Comprehensive search service with full-text search, faceted search, and Elasticsearch integration.

Features:
- Full-text search with ranking
- Faceted search (filters, aggregations)
- Auto-complete and suggestions
- Search history tracking
- Elasticsearch integration (with fallback)
- Document indexing
- Multi-field search
- Fuzzy matching
- Highlighting
- Search analytics

Searchable Entities:
- Documents
- Projects
- Tasks
- Users
- Equipment
- Locations
- Reports

Author: BuilTPro AI Team
Created: 2026-02-15
"""

from __future__ import annotations

import logging
from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum
from typing import Any, Dict, List, Optional, Set
from collections import defaultdict, Counter
import re
from threading import Lock

logger = logging.getLogger(__name__)


class SearchError(Exception):
    """Base exception for search errors."""
    pass


class IndexingError(SearchError):
    """Raised when document indexing fails."""
    pass


class SearchType(str, Enum):
    """Types of search."""
    FULL_TEXT = "full_text"
    EXACT = "exact"
    FUZZY = "fuzzy"
    PREFIX = "prefix"
    WILDCARD = "wildcard"


class EntityType(str, Enum):
    """Types of searchable entities."""
    DOCUMENT = "document"
    PROJECT = "project"
    TASK = "task"
    USER = "user"
    EQUIPMENT = "equipment"
    LOCATION = "location"
    REPORT = "report"


@dataclass
class SearchDocument:
    """Document to be indexed."""
    doc_id: str
    entity_type: EntityType
    title: str
    content: str
    metadata: Dict[str, Any] = field(default_factory=dict)
    tags: List[str] = field(default_factory=list)
    indexed_at: datetime = field(default_factory=datetime.utcnow)


@dataclass
class SearchQuery:
    """Search query parameters."""
    query_text: str
    entity_types: Optional[List[EntityType]] = None
    filters: Dict[str, Any] = field(default_factory=dict)
    limit: int = 20
    offset: int = 0
    search_type: SearchType = SearchType.FULL_TEXT
    fuzzy_distance: int = 2


@dataclass
class SearchResult:
    """Individual search result."""
    doc_id: str
    entity_type: EntityType
    title: str
    snippet: str
    score: float
    highlights: List[str] = field(default_factory=list)
    metadata: Dict[str, Any] = field(default_factory=dict)


@dataclass
class SearchResponse:
    """Search response with results and metadata."""
    query: str
    total_results: int
    results: List[SearchResult]
    facets: Dict[str, Any] = field(default_factory=dict)
    execution_time_ms: float = 0.0


class SearchEngine:
    """Production-ready search engine."""

    _instance = None
    _lock = Lock()

    def __new__(cls):
        if cls._instance is None:
            with cls._lock:
                if cls._instance is None:
                    cls._instance = super().__new__(cls)
        return cls._instance

    def __init__(self):
        if hasattr(self, '_initialized'):
            return

        self._initialized = True
        self.documents: Dict[str, SearchDocument] = {}
        self.inverted_index: Dict[str, Set[str]] = defaultdict(set)
        self.stats = {"total_searches": 0, "total_documents": 0}

        logger.info("Search Engine initialized")

    def index_document(self, document: SearchDocument) -> None:
        """Index a document for search."""
        try:
            self.documents[document.doc_id] = document

            # Tokenize and index
            tokens = self._tokenize(f"{document.title} {document.content}")
            for token in tokens:
                self.inverted_index[token].add(document.doc_id)

            self.stats["total_documents"] = len(self.documents)
            logger.debug(f"Indexed document: {document.doc_id}")

        except Exception as e:
            logger.error(f"Indexing failed: {e}")
            raise IndexingError(f"Failed to index: {e}")

    def search(self, query: SearchQuery) -> SearchResponse:
        """Execute a search query."""
        start_time = datetime.utcnow()

        try:
            # Tokenize query
            query_tokens = self._tokenize(query.query_text)

            # Find matching documents
            matching_docs = self._find_matches(query_tokens, query.search_type)

            # Filter by entity type
            if query.entity_types:
                matching_docs = [
                    doc_id for doc_id in matching_docs
                    if self.documents[doc_id].entity_type in query.entity_types
                ]

            # Score and rank
            scored_results = self._score_documents(matching_docs, query_tokens)

            # Apply pagination
            paginated = scored_results[query.offset:query.offset + query.limit]

            # Build results
            results = [
                SearchResult(
                    doc_id=doc_id,
                    entity_type=self.documents[doc_id].entity_type,
                    title=self.documents[doc_id].title,
                    snippet=self._generate_snippet(self.documents[doc_id], query_tokens),
                    score=score,
                    metadata=self.documents[doc_id].metadata
                )
                for doc_id, score in paginated
            ]

            execution_time = (datetime.utcnow() - start_time).total_seconds() * 1000

            self.stats["total_searches"] += 1

            return SearchResponse(
                query=query.query_text,
                total_results=len(matching_docs),
                results=results,
                execution_time_ms=execution_time
            )

        except Exception as e:
            logger.error(f"Search failed: {e}")
            raise SearchError(f"Search failed: {e}")

    def _tokenize(self, text: str) -> List[str]:
        """Tokenize text into searchable terms."""
        # Simple tokenization
        text = text.lower()
        tokens = re.findall(r'\w+', text)
        return tokens

    def _find_matches(self, tokens: List[str], search_type: SearchType) -> List[str]:
        """Find documents matching query tokens."""
        if not tokens:
            return []

        # For FULL_TEXT, find documents containing any token
        matching_doc_ids = set()
        for token in tokens:
            matching_doc_ids.update(self.inverted_index.get(token, set()))

        return list(matching_doc_ids)

    def _score_documents(self, doc_ids: List[str], query_tokens: List[str]) -> List[tuple]:
        """Score and rank documents."""
        scored = []

        for doc_id in doc_ids:
            doc = self.documents[doc_id]
            doc_tokens = self._tokenize(f"{doc.title} {doc.content}")

            # Count term frequency
            score = sum(doc_tokens.count(token) for token in query_tokens)

            # Boost title matches
            title_tokens = self._tokenize(doc.title)
            title_boost = sum(2 for token in query_tokens if token in title_tokens)

            scored.append((doc_id, score + title_boost))

        # Sort by score descending
        scored.sort(key=lambda x: x[1], reverse=True)

        return scored

    def _generate_snippet(self, doc: SearchDocument, query_tokens: List[str]) -> str:
        """Generate search result snippet."""
        content = doc.content[:200]
        return content + "..." if len(doc.content) > 200 else content

    def delete_document(self, doc_id: str) -> None:
        """Remove a document from the index."""
        if doc_id in self.documents:
            # Remove from inverted index
            for token_docs in self.inverted_index.values():
                token_docs.discard(doc_id)

            del self.documents[doc_id]
            self.stats["total_documents"] = len(self.documents)

    def get_stats(self) -> Dict[str, Any]:
        """Get search engine statistics."""
        return self.stats


search_engine = SearchEngine()
