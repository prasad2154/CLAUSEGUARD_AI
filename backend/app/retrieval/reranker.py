"""
Reranker — Cross-encoder reranking for improved retrieval precision.
Uses sentence-transformers cross-encoder models.
Gracefully degrades if model unavailable.
"""

import logging
from typing import List, TYPE_CHECKING

logger = logging.getLogger(__name__)

_reranker_model = None


def get_reranker():
    """Lazy-load cross-encoder reranker."""
    global _reranker_model
    if _reranker_model is None:
        try:
            from sentence_transformers import CrossEncoder
            _reranker_model = CrossEncoder("cross-encoder/ms-marco-MiniLM-L-6-v2")
            logger.info("Cross-encoder reranker loaded")
        except Exception as e:
            logger.warning(f"Cross-encoder not available: {e}")
            _reranker_model = None
    return _reranker_model


def rerank_clauses(query: str, clauses: list, top_k: int = 5) -> list:
    """
    Rerank retrieved clauses using cross-encoder scoring.
    Falls back to original order if reranker unavailable.
    """
    if not clauses:
        return clauses

    reranker = get_reranker()
    if reranker is None:
        return clauses[:top_k]

    try:
        pairs = [(query, c.clause_text) for c in clauses]
        scores = reranker.predict(pairs)

        # Sort by reranker score
        scored = sorted(zip(clauses, scores), key=lambda x: x[1], reverse=True)
        reranked = [clause for clause, _ in scored[:top_k]]

        # Update scores
        for clause, score in scored[:top_k]:
            clause.score = float(score)

        return reranked

    except Exception as e:
        logger.warning(f"Reranking failed, using vector order: {e}")
        return clauses[:top_k]
