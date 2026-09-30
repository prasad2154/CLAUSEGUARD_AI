"""
Embeddings — Generate vector embeddings for contract clauses.
Uses sentence-transformers locally (no API key required).
Configurable via EMBEDDING_MODEL env var.
"""

import logging
import time
from typing import List, Optional
import numpy as np

from app.config import get_settings

logger = logging.getLogger(__name__)
settings = get_settings()

# Lazy-loaded model to avoid startup delay
_embedding_model = None


def get_embedding_model():
    """Lazy-load and cache the embedding model."""
    global _embedding_model
    if _embedding_model is None:
        try:
            from sentence_transformers import SentenceTransformer
            logger.info(f"Loading embedding model: {settings.embedding_model}")
            _embedding_model = SentenceTransformer(settings.embedding_model)
            logger.info("Embedding model loaded successfully")
        except Exception as e:
            logger.error(f"Failed to load embedding model: {e}")
            raise RuntimeError(f"Embedding model unavailable: {e}")
    return _embedding_model


def embed_text(text: str) -> List[float]:
    """
    Generate embedding for a single text string.
    Returns a list of floats (vector).
    """
    if not text or not text.strip():
        raise ValueError("Cannot embed empty text")

    model = get_embedding_model()
    embedding = model.encode(text, normalize_embeddings=True)
    return embedding.tolist()


def embed_texts(texts: List[str], batch_size: int = 32, show_progress: bool = False) -> List[List[float]]:
    """
    Generate embeddings for multiple texts in batches.
    More efficient than calling embed_text in a loop.
    """
    if not texts:
        return []

    # Filter out empty texts
    valid_texts = [t if t and t.strip() else " " for t in texts]

    model = get_embedding_model()

    start = time.time()
    embeddings = model.encode(
        valid_texts,
        batch_size=batch_size,
        normalize_embeddings=True,
        show_progress_bar=show_progress,
    )
    elapsed = time.time() - start
    logger.info(f"Embedded {len(texts)} texts in {elapsed:.2f}s (batch_size={batch_size})")

    return embeddings.tolist()


def get_embedding_dimension() -> int:
    """Return the embedding dimension for the configured model."""
    return settings.embedding_dimension


def check_embedding_model_available() -> bool:
    """Check if the embedding model can be loaded."""
    try:
        get_embedding_model()
        return True
    except Exception:
        return False
