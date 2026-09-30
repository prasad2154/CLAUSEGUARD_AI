"""
ClauseGuard AI — FastAPI Application Entrypoint
"""

import logging
from contextlib import asynccontextmanager
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse

from app.config import get_settings
from app.database import init_db
from app.retrieval.qdrant_store import ensure_collection_exists

# Import routers
from app.api.health import router as health_router
from app.api.upload import router as upload_router
from app.api.review import router as review_router
from app.api.query import router as query_router
from app.api.comparison import router as compare_router
from app.api.documents import router as documents_router
from app.api.playbook import router as playbook_router
from app.api.metrics import router as metrics_router
from app.api.auth import router as auth_router

# Setup basic logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s"
)
logger = logging.getLogger("clauseguard")
settings = get_settings()

@asynccontextmanager
async def lifespan(app: FastAPI):
    """Lifecycle events for the FastAPI application."""
    logger.info("Starting ClauseGuard AI backend...")
    
    # 1. Initialize Database
    try:
        logger.info("Initializing database...")
        init_db()
    except Exception as e:
        logger.error(f"Database initialization error on startup: {e}")
    
    # 2. Ensure Qdrant collection exists
    try:
        logger.info("Checking Qdrant...")
        ensure_collection_exists()
    except Exception as e:
        logger.warning(f"Qdrant collection check warning: {e}")
    
    logger.info("Backend startup complete.")
    
    yield
    
    logger.info("Shutting down ClauseGuard AI backend...")


app = FastAPI(
    title=settings.app_name,
    version=settings.app_version,
    description="Agentic Contract Risk Detection & Review System",
    lifespan=lifespan
)

# CORS middleware — support local dev origins
cors_origins = list(set(settings.cors_origins_list + [
    "http://localhost:3000",
    "http://localhost:5173",
    "http://localhost:80",
    "http://127.0.0.1:3000",
    "http://127.0.0.1:5173",
    "http://127.0.0.1:80",
    "*"
]))

app.add_middleware(
    CORSMiddleware,
    allow_origins=cors_origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Include routers
app.include_router(health_router)
# Also register health router under /api/health for frontend proxy compatibility
app.include_router(health_router, prefix="/api")
app.include_router(upload_router)
app.include_router(review_router)
app.include_router(query_router)
app.include_router(compare_router)
app.include_router(documents_router)
app.include_router(playbook_router)
app.include_router(metrics_router)
app.include_router(auth_router)

@app.get("/")
def read_root():
    """Root endpoint."""
    return JSONResponse(
        content={
            "app": settings.app_name,
            "version": settings.app_version,
            "status": "online",
            "message": "Visit /docs for API documentation."
        }
    )
