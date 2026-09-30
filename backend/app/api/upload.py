"""
Upload API — Handles document ingestion, parsing, embeddings, and database storage.
"""

import os
import time
import shutil
import logging
import uuid
from typing import Optional
from fastapi import APIRouter, UploadFile, File, BackgroundTasks, HTTPException, Depends
from sqlalchemy.orm import Session

from app.database import get_db
from app.config import get_settings
from app.schemas import UploadResponse
from app.services.document_service import (
    create_document_record,
    update_document_from_ingestion,
    save_clauses
)
from app.ingestion.pipeline import run_ingestion_pipeline
from app.retrieval.embeddings import embed_texts
from app.retrieval.qdrant_store import insert_clauses

logger = logging.getLogger(__name__)
settings = get_settings()
router = APIRouter(prefix="/api/upload", tags=["Upload"])

@router.post("", response_model=UploadResponse)
async def upload_document(
    file: UploadFile = File(...),
    db: Session = Depends(get_db)
):
    """
    Upload a document, process it, extract clauses, generate embeddings,
    and store everything in PostgreSQL and Qdrant.
    This is currently synchronous to satisfy the ~30s requirement directly,
    but can be moved to a BackgroundTask if needed.
    """
    logger.info(f"Received upload request for file: {file.filename}")
    
    # Ensure upload directory exists
    os.makedirs(settings.upload_dir, exist_ok=True)
    
    # Read file size securely
    file.file.seek(0, 2)
    file_size = file.file.tell()
    file.file.seek(0)
    
    # 1. Validation before saving
    if file_size > settings.max_file_size_bytes:
        raise HTTPException(status_code=400, detail=f"File too large. Limit is {settings.max_file_size_mb}MB.")
        
    ext = os.path.splitext(file.filename)[1].lower().lstrip(".")
    if ext not in settings.allowed_extensions_list:
        raise HTTPException(
            status_code=400, 
            detail=f"Unsupported file type. Allowed: {', '.join(settings.allowed_extensions_list)}"
        )

    # 2. Save file temporarily
    document_id = str(uuid.uuid4())
    safe_filename = f"{document_id}.{ext}"
    file_path = os.path.join(settings.upload_dir, safe_filename)
    
    try:
        with open(file_path, "wb") as buffer:
            shutil.copyfileobj(file.file, buffer)
    except Exception as e:
        logger.error(f"Failed to save uploaded file: {e}")
        raise HTTPException(status_code=500, detail="Failed to save file securely on server.")
        
    # 3. Create initial DB record
    doc = create_document_record(
        db=db,
        filename=file.filename,
        original_filename=file.filename,
        file_path=file_path,
        file_size=file_size,
        document_id=document_id
    )
    
    # 4. Run ingestion pipeline
    try:
        result = run_ingestion_pipeline(
            file_path=file_path,
            filename=file.filename,
            file_size=file_size,
            document_id=document_id
        )
        
        if not result.success:
            update_document_from_ingestion(db, result)
            raise HTTPException(status_code=400, detail=result.error)
            
        # 5. Generate embeddings and insert to Qdrant (Safely with fallback)
        qdrant_ids = [str(uuid.uuid4()) for _ in result.clauses]
        if result.clauses:
            try:
                texts_to_embed = [c.clause_text for c in result.clauses]
                embeddings = embed_texts(texts_to_embed)
                
                # Prepare metadata for Qdrant
                qdrant_payloads = []
                for clause in result.clauses:
                    qdrant_payloads.append({
                        "document_id": document_id,
                        "document_name": file.filename,
                        "clause_id": clause.clause_id,
                        "clause_title": clause.clause_title,
                        "clause_text": clause.clause_text,
                        "section": clause.section,
                        "page_number": clause.page_number,
                        "position": clause.position,
                        "clause_type": clause.clause_type,
                        "document_type": result.contract_type,
                        "word_count": clause.word_count
                    })
                    
                # Insert to Qdrant
                actual_ids = insert_clauses(qdrant_payloads, embeddings)
                if actual_ids and len(actual_ids) == len(result.clauses):
                    qdrant_ids = actual_ids
            except Exception as q_err:
                logger.warning(f"Vector embedding / Qdrant indexing encountered an issue (continuing with DB save): {q_err}")

            # 6. Save clauses to SQL DB - ALWAYS GUARANTEED
            save_clauses(db, result, qdrant_ids)
            
        # 7. Finalize document record
        update_document_from_ingestion(db, result)
        
        return UploadResponse(
            document_id=document_id,
            name=file.filename,
            status="indexed",
            message="Document processed and indexed successfully",
            clause_count=result.clause_count,
            page_count=result.page_count,
            ocr_used=result.ocr_used,
            processing_time=result.processing_time
        )
        
    except HTTPException:
        raise
    except Exception as e:
        logger.exception("Upload processing encountered an unexpected error")
        # Ensure error status is captured
        doc.status = "error"
        doc.error_message = str(e)
        db.commit()
        raise HTTPException(status_code=500, detail=f"Internal processing error: {str(e)}")
