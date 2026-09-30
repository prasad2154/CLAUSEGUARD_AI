"""
Retriever — RAG retrieval with reranking.
Retrieves relevant clauses from Qdrant for a given query with DB fallback.
"""

import logging
import time
from typing import List, Optional, Dict, Any

from app.config import get_settings
from app.retrieval.embeddings import embed_text
from app.retrieval.qdrant_store import search_clauses

logger = logging.getLogger(__name__)
settings = get_settings()


class RetrievedClause:
    """A retrieved clause with its relevance score."""

    def __init__(self, data: Dict[str, Any]):
        self.document_id: str = data.get("document_id", "")
        self.document_name: str = data.get("document_name", "")
        self.clause_id: str = data.get("clause_id", "")
        self.clause_title: Optional[str] = data.get("clause_title")
        self.clause_text: str = data.get("clause_text", "")
        self.section: Optional[str] = data.get("section")
        self.page_number: int = data.get("page_number", 1)
        self.clause_type: Optional[str] = data.get("clause_type")
        self.score: float = data.get("score", 0.0)
        self.qdrant_id: str = data.get("qdrant_id", "")

    def to_dict(self) -> Dict[str, Any]:
        return {
            "document_id": self.document_id,
            "document_name": self.document_name,
            "clause_id": self.clause_id,
            "clause_title": self.clause_title,
            "clause_text": self.clause_text,
            "section": self.section,
            "page_number": self.page_number,
            "clause_type": self.clause_type,
            "score": self.score,
        }


def retrieve_clauses(
    query: str,
    document_id: Optional[str] = None,
    top_k: int = None,
    clause_type_filter: Optional[str] = None,
) -> List[RetrievedClause]:
    """
    Retrieve the most relevant clauses for a query.

    Args:
        query: Natural language query
        document_id: Restrict to a specific document (recommended)
        top_k: Number of results
        clause_type_filter: Optional clause type filter

    Returns:
        List of RetrievedClause objects sorted by relevance
    """
    top_k = top_k or settings.retrieval_top_k

    # Generate query embedding
    query_embedding = embed_text(query)

    # Vector search with resilient exception handling
    raw_results = []
    try:
        raw_results = search_clauses(
            query_embedding=query_embedding,
            document_id=document_id,
            top_k=top_k,
            clause_type_filter=clause_type_filter,
        )
    except Exception as e:
        logger.warning(f"Vector search failed, attempting database fallback: {e}")

    # Fallback to database clauses if vector store returned nothing
    if not raw_results and document_id:
        raw_results = _db_clause_fallback(query, document_id, top_k)

    clauses = [RetrievedClause(r) for r in raw_results]

    # Apply reranking if available
    try:
        from app.retrieval.reranker import rerank_clauses
        clauses = rerank_clauses(query, clauses, top_k=settings.rerank_top_k)
    except Exception as e:
        logger.debug(f"Reranking not available, using vector scores: {e}")

    return clauses


def _db_clause_fallback(query: str, document_id: str, top_k: int) -> List[Dict[str, Any]]:
    """Database clause fallback when Qdrant is unavailable."""
    try:
        from app.database import SessionLocal
        from app.models.clause import Clause
        db = SessionLocal()
        try:
            db_clauses = db.query(Clause).filter(Clause.document_id == document_id).all()
            if not db_clauses:
                return []
            
            q_lower = query.lower()
            scored = []
            for c in db_clauses:
                text_lower = (c.clause_text or "").lower()
                matches = sum(1 for word in q_lower.split() if len(word) > 3 and word in text_lower)
                scored.append((matches, {
                    "document_id": c.document_id,
                    "clause_id": c.clause_id,
                    "clause_title": c.clause_title,
                    "clause_text": c.clause_text,
                    "section": c.section,
                    "page_number": c.page_number,
                    "clause_type": c.clause_type,
                    "score": 0.8 + (matches * 0.05),
                    "qdrant_id": getattr(c, "qdrant_id", None) or c.clause_id,
                }))
            scored.sort(key=lambda x: -x[0])
            return [item[1] for item in scored[:top_k]]
        finally:
            db.close()
    except Exception as err:
        logger.error(f"Database clause retrieval fallback failed: {err}")
        return []


def retrieve_all_document_clauses(document_id: str) -> List[Dict[str, Any]]:
    """Retrieve all clauses for a document (used for full-document analysis)."""
    try:
        from app.retrieval.qdrant_store import get_document_clauses_from_qdrant
        clauses = get_document_clauses_from_qdrant(document_id)
        if clauses:
            return clauses
    except Exception as e:
        logger.warning(f"Failed to scroll Qdrant, falling back to DB: {e}")

    # Fallback to DB
    from app.database import SessionLocal
    from app.models.clause import Clause
    db = SessionLocal()
    try:
        db_clauses = db.query(Clause).filter(Clause.document_id == document_id).order_by(Clause.position).all()
        return [
            {
                "document_id": c.document_id,
                "clause_id": c.clause_id,
                "clause_title": c.clause_title,
                "clause_text": c.clause_text,
                "section": c.section,
                "page_number": c.page_number,
                "clause_type": c.clause_type,
                "position": c.position,
                "word_count": c.word_count,
            }
            for c in db_clauses
        ]
    finally:
        db.close()


def validate_citations(citations: List[Dict[str, Any]], document_id: str) -> List[Dict[str, Any]]:
    """
    Validate that citations point to real indexed clauses.
    ANTI-HALLUCINATION: removes any citation not found in vector store or DB.
    """
    if not citations:
        return []

    indexed_clauses = retrieve_all_document_clauses(document_id)
    indexed_ids = {c.get("clause_id") for c in indexed_clauses}

    valid_citations = []
    for citation in citations:
        clause_id = citation.get("clause_id")
        if clause_id and clause_id in indexed_ids:
            actual_clause = next(
                (c for c in indexed_clauses if c.get("clause_id") == clause_id),
                None,
            )
            if actual_clause:
                citation["text"] = actual_clause.get("clause_text", citation.get("text", ""))
                citation["page"] = actual_clause.get("page_number", citation.get("page", 1))
                citation["section"] = actual_clause.get("section", citation.get("section"))
                valid_citations.append(citation)
        else:
            logger.warning(f"Citation {clause_id} not found in indexed document — REMOVED (anti-hallucination)")

    return valid_citations
