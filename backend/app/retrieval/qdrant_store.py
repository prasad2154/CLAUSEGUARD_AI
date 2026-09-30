"""
Qdrant Vector Store — Manage contract clause embeddings in Qdrant.

Operations:
- Create/ensure collection exists
- Insert clause embeddings with metadata
- Similarity search with document filtering
- Delete by document ID
- Health check
"""

import logging
import time
import uuid
from typing import List, Optional, Dict, Any

from app.config import get_settings

logger = logging.getLogger(__name__)
settings = get_settings()

# Lazy-loaded client
_qdrant_client = None
_is_embedded_mode = False


def get_qdrant_client():
    """
    Lazy-load and cache the Qdrant client.
    Supports:
    1. Remote Docker/Host Qdrant (settings.qdrant_host)
    2. Localhost Qdrant fallback (if 'qdrant' hostname unresolvable on host machine)
    3. Embedded local directory fallback (if no Qdrant server is running)
    4. In-memory fallback (guarantees zero crashes)
    """
    global _qdrant_client, _is_embedded_mode
    if _qdrant_client is not None:
        return _qdrant_client

    import socket
    import os
    from qdrant_client import QdrantClient

    # 1. Determine host to try
    host_to_try = settings.qdrant_host
    can_resolve = False
    try:
        socket.gethostbyname(host_to_try)
        can_resolve = True
    except Exception:
        can_resolve = False

    # If configured host is 'qdrant' and unresolvable (e.g. running outside Docker on Windows), try localhost
    if not can_resolve and host_to_try == "qdrant":
        logger.info("Host 'qdrant' cannot be resolved via DNS. Attempting 'localhost'...")
        host_to_try = "localhost"
        try:
            socket.gethostbyname(host_to_try)
            can_resolve = True
        except Exception:
            can_resolve = False

    if can_resolve:
        try:
            logger.info(f"Attempting remote Qdrant connection at {host_to_try}:{settings.qdrant_port}...")
            client = QdrantClient(
                host=host_to_try,
                port=settings.qdrant_port,
                api_key=settings.qdrant_api_key,
                timeout=3,
            )
            # Test connectivity
            client.get_collections()
            _qdrant_client = client
            _is_embedded_mode = False
            logger.info(f"Connected successfully to remote Qdrant at {host_to_try}:{settings.qdrant_port}")
            return _qdrant_client
        except Exception as e:
            logger.warning(f"Remote Qdrant connection to {host_to_try}:{settings.qdrant_port} failed: {e}")

    # 2. Fall back to embedded local storage (no external daemon required)
    try:
        backend_dir = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", ".."))
        local_qdrant_path = os.path.join(backend_dir, "qdrant_local_data")
        os.makedirs(local_qdrant_path, exist_ok=True)
        logger.info(f"Initializing embedded persistent Qdrant at {local_qdrant_path}")
        _qdrant_client = QdrantClient(path=local_qdrant_path)
        _is_embedded_mode = True
        return _qdrant_client
    except Exception as e_embed:
        logger.warning(f"Embedded local Qdrant failed ({e_embed}), falling back to in-memory mode...")
        try:
            _qdrant_client = QdrantClient(location=":memory:")
            _is_embedded_mode = True
            logger.info("In-memory Qdrant client initialized successfully.")
            return _qdrant_client
        except Exception as e_mem:
            logger.error(f"In-memory Qdrant initialization failed: {e_mem}")
            raise


def ensure_collection_exists(dimension: int = None) -> bool:
    """
    Ensure the clause collection exists in Qdrant.
    Creates it with proper config if it doesn't exist.
    """
    from qdrant_client.models import (
        Distance,
        VectorParams,
        OptimizersConfigDiff,
    )

    dimension = dimension or settings.embedding_dimension
    collection_name = settings.qdrant_collection

    try:
        client = get_qdrant_client()
        collections = client.get_collections()
        existing = [c.name for c in collections.collections]

        if collection_name not in existing:
            logger.info(f"Creating Qdrant collection: {collection_name} (dim={dimension})")
            client.create_collection(
                collection_name=collection_name,
                vectors_config=VectorParams(
                    size=dimension,
                    distance=Distance.COSINE,
                ),
            )
            logger.info(f"Collection '{collection_name}' created successfully")
        else:
            logger.debug(f"Collection '{collection_name}' already exists")

        return True

    except Exception as e:
        logger.error(f"Failed to ensure Qdrant collection: {e}")
        return False


def insert_clauses(
    clauses_data: List[Dict[str, Any]],
    embeddings: List[List[float]],
) -> List[str]:
    """
    Insert clause embeddings into Qdrant.

    Args:
        clauses_data: List of clause metadata dicts
        embeddings: Corresponding list of embedding vectors

    Returns:
        List of Qdrant point IDs
    """
    from qdrant_client.models import PointStruct

    if len(clauses_data) != len(embeddings):
        raise ValueError("clauses_data and embeddings must have the same length")

    point_ids = [str(uuid.uuid4()) for _ in clauses_data]

    try:
        dim = len(embeddings[0]) if embeddings else settings.embedding_dimension
        ensure_collection_exists(dim)
        client = get_qdrant_client()
        collection_name = settings.qdrant_collection

        points = []
        for pid, clause_data, embedding in zip(point_ids, clauses_data, embeddings):
            payload = {
                "document_id": clause_data.get("document_id", ""),
                "document_name": clause_data.get("document_name", ""),
                "clause_id": clause_data.get("clause_id", ""),
                "clause_title": clause_data.get("clause_title"),
                "clause_text": clause_data.get("clause_text", ""),
                "section": clause_data.get("section"),
                "page_number": clause_data.get("page_number", 1),
                "position": clause_data.get("position", 0),
                "clause_type": clause_data.get("clause_type"),
                "document_type": clause_data.get("document_type"),
                "word_count": clause_data.get("word_count", 0),
            }

            points.append(PointStruct(
                id=pid,
                vector=embedding,
                payload=payload,
            ))

        # Batch upsert
        BATCH_SIZE = 100
        for i in range(0, len(points), BATCH_SIZE):
            batch = points[i:i + BATCH_SIZE]
            client.upsert(
                collection_name=collection_name,
                points=batch,
            )

        logger.info(f"Inserted {len(points)} clauses into Qdrant collection '{collection_name}'")
    except Exception as e:
        logger.error(f"Failed to upsert points to Qdrant (continuing with generated IDs): {e}")

    return point_ids


def search_clauses(
    query_embedding: List[float],
    document_id: Optional[str] = None,
    top_k: int = 10,
    clause_type_filter: Optional[str] = None,
) -> List[Dict[str, Any]]:
    """
    Search for relevant clauses using vector similarity.

    Args:
        query_embedding: Query vector
        document_id: If provided, restrict search to this document
        top_k: Number of results to return
        clause_type_filter: Optional clause type filter

    Returns:
        List of clause results with scores and metadata
    """
    try:
        from qdrant_client.models import Filter, FieldCondition, MatchValue

        client = get_qdrant_client()
        collection_name = settings.qdrant_collection

        # Build filter conditions
        filter_conditions = []

        if document_id:
            filter_conditions.append(
                FieldCondition(key="document_id", match=MatchValue(value=document_id))
            )

        if clause_type_filter:
            filter_conditions.append(
                FieldCondition(key="clause_type", match=MatchValue(value=clause_type_filter))
            )

        query_filter = None
        if filter_conditions:
            query_filter = Filter(must=filter_conditions)

        results = client.search(
            collection_name=collection_name,
            query_vector=query_embedding,
            limit=top_k,
            query_filter=query_filter,
            with_payload=True,
            with_vectors=False,
        )

        return [
            {
                "score": hit.score,
                "qdrant_id": str(hit.id),
                **hit.payload,
            }
            for hit in results
        ]
    except Exception as e:
        logger.warning(f"Qdrant search failed, returning empty list: {e}")
        return []


def delete_document_clauses(document_id: str) -> bool:
    """Delete all clause vectors for a given document."""
    try:
        from qdrant_client.models import Filter, FieldCondition, MatchValue

        client = get_qdrant_client()
        collection_name = settings.qdrant_collection

        client.delete(
            collection_name=collection_name,
            points_selector=Filter(
                must=[FieldCondition(key="document_id", match=MatchValue(value=document_id))]
            ),
        )
        logger.info(f"Deleted Qdrant vectors for document: {document_id}")
        return True
    except Exception as e:
        logger.warning(f"Failed to delete Qdrant vectors for {document_id}: {e}")
        return False


def get_document_clauses_from_qdrant(document_id: str, limit: int = 500) -> List[Dict[str, Any]]:
    """Retrieve all clauses for a document from Qdrant (by scroll)."""
    try:
        from qdrant_client.models import Filter, FieldCondition, MatchValue

        client = get_qdrant_client()
        collection_name = settings.qdrant_collection

        results = []
        offset = None

        while True:
            records, next_offset = client.scroll(
                collection_name=collection_name,
                scroll_filter=Filter(
                    must=[FieldCondition(key="document_id", match=MatchValue(value=document_id))]
                ),
                limit=100,
                offset=offset,
                with_payload=True,
                with_vectors=False,
            )

            results.extend([{"qdrant_id": str(r.id), **r.payload} for r in records])

            if next_offset is None or len(results) >= limit:
                break
            offset = next_offset

        return sorted(results, key=lambda x: x.get("position", 0))
    except Exception as e:
        logger.warning(f"Failed to scroll Qdrant clauses for {document_id}: {e}")
        return []


def check_qdrant_health() -> Dict[str, Any]:
    """Check Qdrant connection and collection status."""
    start = time.time()
    try:
        client = get_qdrant_client()
        info = client.get_collections()
        latency = (time.time() - start) * 1000
        collection_names = [c.name for c in info.collections]
        has_collection = settings.qdrant_collection in collection_names
        mode_str = "embedded" if _is_embedded_mode else "network"
        return {
            "healthy": True,
            "latency_ms": round(latency, 1),
            "collections": collection_names,
            "has_clause_collection": has_collection,
            "mode": mode_str,
        }
    except Exception as e:
        return {
            "healthy": False,
            "error": str(e),
            "latency_ms": (time.time() - start) * 1000,
        }
