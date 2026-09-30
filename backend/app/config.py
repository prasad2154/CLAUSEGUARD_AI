"""
ClauseGuard AI — Application Configuration
All configuration sourced from environment variables.
No secrets in source code.
"""

from functools import lru_cache
from typing import List, Optional
from pydantic_settings import BaseSettings, SettingsConfigDict
from pydantic import Field, field_validator


class Settings(BaseSettings):
    model_config = SettingsConfigDict(
        env_file=(".env", "../.env"),
        env_file_encoding="utf-8",
        case_sensitive=False,
        extra="ignore",
    )

    # ── Application ──────────────────────────────────────────────────────────
    app_name: str = "ClauseGuard AI"
    app_version: str = "1.0.0"
    debug: bool = False
    backend_host: str = "0.0.0.0"
    backend_port: int = 8000
    secret_key: str = "change-this-in-production"

    # ── CORS ──────────────────────────────────────────────────────────────────
    cors_origins: str = "http://localhost:3000,http://localhost:5173,http://localhost:80"

    @property
    def cors_origins_list(self) -> List[str]:
        return [o.strip() for o in self.cors_origins.split(",")]

    # ── LLM Configuration ─────────────────────────────────────────────────────
    llm_provider: str = "openai"
    openai_api_key: Optional[str] = None
    openai_base_url: str = "https://api.openai.com/v1"
    llm_model: str = "gpt-4o-mini"
    llm_temperature: float = 0.1
    llm_max_tokens: int = 4096

    # ── Embeddings ────────────────────────────────────────────────────────────
    embedding_model: str = "all-MiniLM-L6-v2"
    embedding_dimension: int = 384

    # ── Database ──────────────────────────────────────────────────────────────
    database_url: str = "postgresql://clauseguard:clauseguard@localhost:5432/clauseguard"

    # ── Qdrant ────────────────────────────────────────────────────────────────
    qdrant_host: str = "localhost"
    qdrant_port: int = 6333
    qdrant_collection: str = "contract_clauses"
    qdrant_api_key: Optional[str] = None

    # ── File Upload ───────────────────────────────────────────────────────────
    upload_dir: str = "./uploads"
    max_file_size_mb: int = 50
    allowed_extensions: str = "pdf,docx,doc,png,jpg,jpeg,tiff"

    @property
    def max_file_size_bytes(self) -> int:
        return self.max_file_size_mb * 1024 * 1024

    @property
    def allowed_extensions_list(self) -> List[str]:
        return [e.strip().lower() for e in self.allowed_extensions.split(",")]

    # ── OCR ───────────────────────────────────────────────────────────────────
    ocr_confidence_threshold: int = 60
    min_text_length_for_ocr_skip: int = 100
    tesseract_lang: str = "eng"

    # ── Processing ────────────────────────────────────────────────────────────
    max_clauses_per_doc: int = 500
    clause_min_length: int = 50
    clause_max_length: int = 3000
    retrieval_top_k: int = 10
    rerank_top_k: int = 5

    # ── Logging ───────────────────────────────────────────────────────────────
    log_level: str = "INFO"


@lru_cache()
def get_settings() -> Settings:
    """Cached settings singleton."""
    return Settings()
