"""
ClauseGuard AI — Database Setup
SQLAlchemy + PostgreSQL / SQLite with resilient startup and session management.
"""

import time
import logging
from typing import Generator
from sqlalchemy import create_engine, text
from sqlalchemy.orm import sessionmaker, DeclarativeBase, Session
from app.config import get_settings

logger = logging.getLogger(__name__)
settings = get_settings()


class Base(DeclarativeBase):
    """SQLAlchemy declarative base for all models."""
    pass


import os

# Compute reliable path to fallback SQLite database
_backend_root = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
_fallback_path = os.path.join(_backend_root, "clauseguard_fallback.db").replace("\\", "/")
FALLBACK_SQLITE_URL = f"sqlite:///{_fallback_path}"


def _create_db_engine(db_url: str):
    is_sqlite = db_url.startswith("sqlite")
    connect_args = {"check_same_thread": False} if is_sqlite else {}
    kwargs = {
        "echo": settings.debug,
        "connect_args": connect_args,
    }
    if not is_sqlite:
        kwargs.update({
            "pool_pre_ping": True,
            "pool_size": 10,
            "max_overflow": 20,
        })
    try:
        return create_engine(db_url, **kwargs)
    except (ImportError, Exception) as e:
        logger.warning(
            f"Failed to initialize database driver for {db_url} ({e}). "
            f"Falling back to local SQLite ({FALLBACK_SQLITE_URL})."
        )
        return create_engine(
            FALLBACK_SQLITE_URL, 
            echo=settings.debug, 
            connect_args={"check_same_thread": False}
        )


engine = _create_db_engine(settings.database_url)

SessionLocal = sessionmaker(
    autocommit=False,
    autoflush=False,
    bind=engine,
)


def get_db() -> Generator[Session, None, None]:
    """FastAPI dependency — yields a database session."""
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


def init_db(max_retries: int = 5, retry_delay: float = 2.0) -> None:
    """Create all tables with retry logic and SQLite fallback for local development."""
    global engine, SessionLocal
    
    # Import all models so they register with Base.metadata
    from app.models import document, clause, review, risk, query, comparison, playbook  # noqa: F401

    last_error = None
    for attempt in range(1, max_retries + 1):
        try:
            logger.info(f"Database connection attempt {attempt}/{max_retries}...")
            with engine.connect() as conn:
                conn.execute(text("SELECT 1"))
            Base.metadata.create_all(bind=engine)
            logger.info("Database initialized and tables verified.")
            return
        except Exception as e:
            last_error = e
            logger.warning(f"Database initialization attempt {attempt} failed: {e}")
            if attempt < max_retries:
                time.sleep(retry_delay)

    # If Postgres was specified but unreachable, check if we can fall back to local SQLite in dev
    if not settings.database_url.startswith("sqlite"):
        logger.warning(
            f"Primary database ({settings.database_url}) unavailable. "
            "Falling back to local SQLite (sqlite:///./clauseguard_fallback.db) for local run..."
        )
        try:
            fallback_url = "sqlite:///./clauseguard_fallback.db"
            engine = _create_db_engine(fallback_url)
            SessionLocal.configure(bind=engine)
            Base.metadata.create_all(bind=engine)
            logger.info("Fallback SQLite database initialized successfully.")
            return
        except Exception as fallback_err:
            logger.error(f"Fallback SQLite database failed: {fallback_err}")

    raise RuntimeError(f"Could not initialize database after {max_retries} attempts: {last_error}")


def check_db_connection() -> bool:
    """Check if database is reachable (used in health endpoint)."""
    try:
        with engine.connect() as conn:
            conn.execute(text("SELECT 1"))
        return True
    except Exception:
        return False
