"""
Health API — System health and dependency checking.
"""

from datetime import datetime
from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from app.database import get_db, check_db_connection
from app.config import get_settings
from app.schemas import HealthResponse, ServiceStatus
from app.retrieval.qdrant_store import check_qdrant_health
from app.agents.llm_client import check_llm_available
from app.retrieval.embeddings import check_embedding_model_available
from app.ingestion.ocr_processor import check_tesseract_available

router = APIRouter(prefix="/health", tags=["Health"])
settings = get_settings()

@router.get("", response_model=HealthResponse)
async def get_health():
    """
    Check health status of all dependent services:
    - FastAPI Backend
    - PostgreSQL Database
    - Qdrant Vector DB
    - LLM Provider
    - Embedding Model
    - OCR (Tesseract)
    """
    services = []
    
    # 1. Database
    db_ok = check_db_connection()
    services.append(ServiceStatus(
        name="PostgreSQL",
        status="healthy" if db_ok else "offline",
        details="Connected to metadata database" if db_ok else "Connection failed"
    ))
    
    # 2. Qdrant
    qdrant_health = check_qdrant_health()
    services.append(ServiceStatus(
        name="Qdrant",
        status="healthy" if qdrant_health.get("healthy") else "offline",
        latency_ms=qdrant_health.get("latency_ms"),
        details=f"Connected ({qdrant_health.get('mode', 'network')})" if qdrant_health.get("healthy") else qdrant_health.get("error")
    ))
    
    # 3. LLM
    llm_health = check_llm_available()
    services.append(ServiceStatus(
        name="LLM Provider",
        status="healthy" if llm_health.get("available") else "degraded",
        latency_ms=llm_health.get("latency_ms"),
        details=f"Model: {llm_health.get('model')}" + (f" - Error: {llm_health.get('error')}" if not llm_health.get("available") else "")
    ))
    
    # 4. Embeddings
    emb_ok = check_embedding_model_available()
    services.append(ServiceStatus(
        name="Embedding Model",
        status="healthy" if emb_ok else "degraded",
        details=f"Local model: {settings.embedding_model}"
    ))
    
    # 5. OCR
    ocr_ok = check_tesseract_available()
    services.append(ServiceStatus(
        name="OCR (Tesseract)",
        status="healthy" if ocr_ok else "offline",
        details="Available for scanned PDFs/Images" if ocr_ok else "Not installed"
    ))
    
    # Determine overall status
    statuses = [s.status for s in services]
    if "offline" in statuses:
        overall_status = "degraded"
    elif "degraded" in statuses:
        overall_status = "degraded"
    else:
        overall_status = "healthy"
        
    return HealthResponse(
        status=overall_status,
        version=settings.app_version,
        timestamp=datetime.utcnow(),
        services=services
    )
