import os
import uuid
import logging
from typing import List
from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session

from app.database import get_db
from app.schemas import DocumentResponse, DocumentListResponse, ClauseResponse
from app.services.document_service import (
    get_documents, 
    get_document_count, 
    get_document, 
    delete_document, 
    get_document_clauses,
    save_clauses,
    update_document_from_ingestion
)
from app.ingestion.pipeline import run_ingestion_pipeline
from app.retrieval.embeddings import embed_texts
from app.retrieval.qdrant_store import insert_clauses

logger = logging.getLogger(__name__)
router = APIRouter(prefix="/api/documents", tags=["Documents"])


def reprocess_document_internal(db: Session, doc) -> bool:
    """Helper to reprocess a document from its stored file."""
    if not doc.file_path or not os.path.exists(doc.file_path):
        logger.warning(f"File for document {doc.id} not found at {doc.file_path}")
        return False

    try:
        file_size = os.path.getsize(doc.file_path)
        result = run_ingestion_pipeline(
            file_path=doc.file_path,
            filename=doc.original_filename or doc.name,
            file_size=file_size,
            document_id=doc.id
        )

        if not result.success or not result.clauses:
            logger.warning(f"Reprocess pipeline failed for {doc.id}: {result.error}")
            update_document_from_ingestion(db, result)
            return False

        qdrant_ids = [str(uuid.uuid4()) for _ in result.clauses]
        try:
            texts_to_embed = [c.clause_text for c in result.clauses]
            embeddings = embed_texts(texts_to_embed)
            qdrant_payloads = [{
                "document_id": doc.id,
                "document_name": doc.name,
                "clause_id": c.clause_id,
                "clause_title": c.clause_title,
                "clause_text": c.clause_text,
                "section": c.section,
                "page_number": c.page_number,
                "position": c.position,
                "clause_type": c.clause_type,
                "document_type": result.contract_type,
                "word_count": c.word_count
            } for c in result.clauses]
            actual_ids = insert_clauses(qdrant_payloads, embeddings)
            if actual_ids and len(actual_ids) == len(result.clauses):
                qdrant_ids = actual_ids
        except Exception as e:
            logger.warning(f"Vector embedding during reprocess warning: {e}")

        save_clauses(db, result, qdrant_ids)
        update_document_from_ingestion(db, result)
        logger.info(f"Successfully reprocessed document {doc.id} ({result.clause_count} clauses)")
        return True
    except Exception as e:
        logger.error(f"Error during reprocess for {doc.id}: {e}")
        return False


@router.get("", response_model=DocumentListResponse)
async def list_documents(
    skip: int = Query(0, ge=0),
    limit: int = Query(100, ge=1, le=500),
    db: Session = Depends(get_db)
):
    """List all documents with pagination."""
    docs = get_documents(db, skip=skip, limit=limit)
    total = get_document_count(db)
    
    return DocumentListResponse(
        documents=docs,
        total=total,
        page=(skip // limit) + 1,
        page_size=limit
    )


@router.get("/{document_id}", response_model=DocumentResponse)
async def retrieve_document(document_id: str, db: Session = Depends(get_db)):
    """Get document metadata by ID."""
    doc = get_document(db, document_id)
    if not doc:
        raise HTTPException(status_code=404, detail="Document not found")
        
    # Auto-heal: If document was in error status or has 0 clauses, attempt reprocess if file exists
    if (doc.status == "error" or doc.clause_count == 0) and doc.file_path and os.path.exists(doc.file_path):
        logger.info(f"Auto-healing document {doc.id}...")
        if reprocess_document_internal(db, doc):
            doc = get_document(db, document_id)
            
    return doc


@router.post("/{document_id}/reprocess", response_model=DocumentResponse)
async def reprocess_document(document_id: str, db: Session = Depends(get_db)):
    """Manually reprocess a document to re-extract clauses and embeddings."""
    doc = get_document(db, document_id)
    if not doc:
        raise HTTPException(status_code=404, detail="Document not found")
    success = reprocess_document_internal(db, doc)
    if not success:
        raise HTTPException(status_code=400, detail="Failed to reprocess document from source file")
    return get_document(db, document_id)


@router.get("/{document_id}/clauses", response_model=List[ClauseResponse])
async def retrieve_document_clauses(document_id: str, db: Session = Depends(get_db)):
    """Get all parsed clauses for a document."""
    doc = get_document(db, document_id)
    if not doc:
        raise HTTPException(status_code=404, detail="Document not found")
    clauses = get_document_clauses(db, document_id)
    
    # Auto-heal clauses if empty but file exists
    if not clauses and doc.file_path and os.path.exists(doc.file_path):
        logger.info(f"Clauses empty for {document_id}. Triggering auto-reprocessing...")
        if reprocess_document_internal(db, doc):
            clauses = get_document_clauses(db, document_id)
            
    return clauses


@router.delete("/{document_id}")
async def remove_document(document_id: str, db: Session = Depends(get_db)):
    """Delete a document, its file, clauses, vector embeddings, and reviews."""
    success = delete_document(db, document_id)
    if not success:
        raise HTTPException(status_code=404, detail="Document not found")
    return {"status": "success", "message": "Document deleted completely"}

