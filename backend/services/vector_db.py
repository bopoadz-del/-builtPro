# Vector Database Integration - ITEM 130
# Semantic search and similarity matching using vector embeddings

from typing import List, Dict, Optional, Tuple, Any
from dataclasses import dataclass
import numpy as np
from datetime import datetime
import json

from ..core.logging_config import get_logger

logger = get_logger(__name__)

# Try to import vector database libraries
try:
    import chromadb
    from chromadb.config import Settings
    CHROMA_AVAILABLE = True
except ImportError:
    chromadb = None
    CHROMA_AVAILABLE = False
    logger.info("ChromaDB not installed - using fallback vector storage")


@dataclass
class VectorDocument:
    """Document with vector embedding."""
    id: str
    content: str
    embedding: List[float]
    metadata: Dict[str, Any]
    created_at: datetime = None

    def __post_init__(self):
        if self.created_at is None:
            self.created_at = datetime.utcnow()


class VectorDatabase:
    """
    Vector database for semantic search and similarity matching.

    Uses ChromaDB when available, falls back to in-memory similarity search.
    """

    def __init__(
        self,
        collection_name: str = "cerebrum",
        persist_directory: Optional[str] = None
    ):
        """
        Initialize vector database.

        Args:
            collection_name: Name of the collection
            persist_directory: Directory for persistence (ChromaDB only)
        """
        self.collection_name = collection_name
        self.persist_directory = persist_directory
        self.client = None
        self.collection = None
        self.fallback_storage: List[VectorDocument] = []
        self.logger = get_logger(self.__class__.__name__)

        self._initialize()

    def _initialize(self):
        """Initialize the vector database."""
        if CHROMA_AVAILABLE and chromadb is not None:
            try:
                if self.persist_directory:
                    self.client = chromadb.Client(Settings(
                        chroma_db_impl="duckdb+parquet",
                        persist_directory=self.persist_directory
                    ))
                else:
                    self.client = chromadb.Client()

                self.collection = self.client.get_or_create_collection(
                    name=self.collection_name,
                    metadata={"description": "Cerebrum document embeddings"}
                )

                self.logger.info(f"Initialized ChromaDB collection: {self.collection_name}")
                return

            except Exception as e:
                self.logger.warning(f"Failed to initialize ChromaDB: {e}")

        self.logger.info("Using fallback in-memory vector storage")

    def add_documents(
        self,
        documents: List[VectorDocument]
    ) -> bool:
        """
        Add documents to the vector database.

        Args:
            documents: List of vector documents to add

        Returns:
            True if successful
        """
        try:
            if self.collection is not None:
                # Use ChromaDB
                self.collection.add(
                    ids=[doc.id for doc in documents],
                    embeddings=[doc.embedding for doc in documents],
                    documents=[doc.content for doc in documents],
                    metadatas=[doc.metadata for doc in documents]
                )
                self.logger.info(f"Added {len(documents)} documents to ChromaDB")
                return True

            else:
                # Use fallback storage
                self.fallback_storage.extend(documents)
                self.logger.info(f"Added {len(documents)} documents to fallback storage")
                return True

        except Exception as e:
            self.logger.error(f"Failed to add documents: {e}")
            return False

    def search(
        self,
        query_embedding: List[float],
        limit: int = 10,
        filter_metadata: Optional[Dict[str, Any]] = None
    ) -> List[Dict[str, Any]]:
        """
        Search for similar documents using vector similarity.

        Args:
            query_embedding: Query vector
            limit: Maximum number of results
            filter_metadata: Optional metadata filters

        Returns:
            List of matching documents with scores
        """
        try:
            if self.collection is not None:
                # Use ChromaDB
                results = self.collection.query(
                    query_embeddings=[query_embedding],
                    n_results=limit,
                    where=filter_metadata
                )

                # Format results
                formatted_results = []
                for i in range(len(results['ids'][0])):
                    formatted_results.append({
                        'id': results['ids'][0][i],
                        'content': results['documents'][0][i],
                        'metadata': results['metadatas'][0][i],
                        'distance': results['distances'][0][i],
                        'score': 1 - results['distances'][0][i]  # Convert distance to similarity score
                    })

                return formatted_results

            else:
                # Use fallback - cosine similarity
                return self._fallback_search(query_embedding, limit, filter_metadata)

        except Exception as e:
            self.logger.error(f"Search failed: {e}")
            return []

    def _fallback_search(
        self,
        query_embedding: List[float],
        limit: int,
        filter_metadata: Optional[Dict[str, Any]] = None
    ) -> List[Dict[str, Any]]:
        """Fallback similarity search using cosine similarity."""
        query_vec = np.array(query_embedding)

        results = []
        for doc in self.fallback_storage:
            # Apply metadata filter
            if filter_metadata:
                if not all(doc.metadata.get(k) == v for k, v in filter_metadata.items()):
                    continue

            # Calculate cosine similarity
            doc_vec = np.array(doc.embedding)
            similarity = np.dot(query_vec, doc_vec) / (
                np.linalg.norm(query_vec) * np.linalg.norm(doc_vec)
            )

            results.append({
                'id': doc.id,
                'content': doc.content,
                'metadata': doc.metadata,
                'score': float(similarity),
                'distance': 1 - float(similarity)
            })

        # Sort by similarity (descending)
        results.sort(key=lambda x: x['score'], reverse=True)
        return results[:limit]

    def delete_documents(self, document_ids: List[str]) -> bool:
        """
        Delete documents by ID.

        Args:
            document_ids: List of document IDs to delete

        Returns:
            True if successful
        """
        try:
            if self.collection is not None:
                self.collection.delete(ids=document_ids)
                self.logger.info(f"Deleted {len(document_ids)} documents from ChromaDB")
                return True
            else:
                self.fallback_storage = [
                    doc for doc in self.fallback_storage
                    if doc.id not in document_ids
                ]
                self.logger.info(f"Deleted {len(document_ids)} documents from fallback storage")
                return True

        except Exception as e:
            self.logger.error(f"Failed to delete documents: {e}")
            return False

    def get_document(self, document_id: str) -> Optional[Dict[str, Any]]:
        """
        Get a document by ID.

        Args:
            document_id: Document ID

        Returns:
            Document data if found, None otherwise
        """
        try:
            if self.collection is not None:
                result = self.collection.get(ids=[document_id])
                if result['ids']:
                    return {
                        'id': result['ids'][0],
                        'content': result['documents'][0],
                        'metadata': result['metadatas'][0],
                        'embedding': result['embeddings'][0] if result.get('embeddings') else None
                    }
            else:
                for doc in self.fallback_storage:
                    if doc.id == document_id:
                        return {
                            'id': doc.id,
                            'content': doc.content,
                            'metadata': doc.metadata,
                            'embedding': doc.embedding
                        }

            return None

        except Exception as e:
            self.logger.error(f"Failed to get document: {e}")
            return None

    def count_documents(self, filter_metadata: Optional[Dict[str, Any]] = None) -> int:
        """
        Count documents in the collection.

        Args:
            filter_metadata: Optional metadata filter

        Returns:
            Number of documents
        """
        try:
            if self.collection is not None:
                if filter_metadata:
                    result = self.collection.count(where=filter_metadata)
                else:
                    result = self.collection.count()
                return result
            else:
                if filter_metadata:
                    return sum(
                        1 for doc in self.fallback_storage
                        if all(doc.metadata.get(k) == v for k, v in filter_metadata.items())
                    )
                return len(self.fallback_storage)

        except Exception as e:
            self.logger.error(f"Failed to count documents: {e}")
            return 0

    def update_document(
        self,
        document_id: str,
        content: Optional[str] = None,
        embedding: Optional[List[float]] = None,
        metadata: Optional[Dict[str, Any]] = None
    ) -> bool:
        """
        Update a document.

        Args:
            document_id: Document ID
            content: Optional new content
            embedding: Optional new embedding
            metadata: Optional new metadata

        Returns:
            True if successful
        """
        try:
            if self.collection is not None:
                update_data = {'ids': [document_id]}
                if content is not None:
                    update_data['documents'] = [content]
                if embedding is not None:
                    update_data['embeddings'] = [embedding]
                if metadata is not None:
                    update_data['metadatas'] = [metadata]

                self.collection.update(**update_data)
                return True
            else:
                for doc in self.fallback_storage:
                    if doc.id == document_id:
                        if content is not None:
                            doc.content = content
                        if embedding is not None:
                            doc.embedding = embedding
                        if metadata is not None:
                            doc.metadata = metadata
                        return True
                return False

        except Exception as e:
            self.logger.error(f"Failed to update document: {e}")
            return False

    def clear_collection(self) -> bool:
        """
        Clear all documents from the collection.

        Returns:
            True if successful
        """
        try:
            if self.collection is not None:
                # Delete and recreate collection
                self.client.delete_collection(name=self.collection_name)
                self.collection = self.client.create_collection(
                    name=self.collection_name
                )
                return True
            else:
                self.fallback_storage.clear()
                return True

        except Exception as e:
            self.logger.error(f"Failed to clear collection: {e}")
            return False


# Singleton instances
_vector_dbs: Dict[str, VectorDatabase] = {}


def get_vector_db(
    collection_name: str = "cerebrum",
    persist_directory: Optional[str] = None
) -> VectorDatabase:
    """
    Get or create vector database instance.

    Args:
        collection_name: Collection name
        persist_directory: Optional persistence directory

    Returns:
        Vector database instance
    """
    if collection_name not in _vector_dbs:
        _vector_dbs[collection_name] = VectorDatabase(
            collection_name=collection_name,
            persist_directory=persist_directory
        )

    return _vector_dbs[collection_name]
