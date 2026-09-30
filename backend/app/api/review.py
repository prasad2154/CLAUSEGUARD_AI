"""
Review API — Trigger agentic AI reviews and fetch review results.
"""

import time
import logging
from typing import Optional
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from app.database import get_db
from app.schemas import ReviewRequest, ReviewResponse
from app.services.document_service import get_document, get_document_clauses
from app.services.review_service import save_review_report, get_latest_review
from app.agents.orchestrator import run_agentic_review
from app.review.report_generator import generate_review_report
logger = logging.getLogger(__name__)
router = APIRouter(prefix="/api/review", tags=["Review"])

@router.post("", response_model=ReviewResponse)
async def trigger_review(
    request: ReviewRequest,
    db: Session = Depends(get_db)
):
    """
    Trigger the agentic AI contract review workflow.
    """
    logger.info(f"Triggering review for document {request.document_id}")
    start_time = time.time()
    
    # 1. Validate document exists
    doc = get_document(db, request.document_id)
    if not doc:
        raise HTTPException(status_code=404, detail="Document not found")

    # Auto-heal: If document failed earlier or has 0 clauses, attempt to reprocess from file
    clauses = get_document_clauses(db, request.document_id)
    if (doc.status == "error" or not clauses) and doc.file_path:
        from app.api.documents import reprocess_document_internal
        logger.info(f"Triggering auto-heal for document {doc.id} before review...")
        if reprocess_document_internal(db, doc):
            doc = get_document(db, request.document_id)
            clauses = get_document_clauses(db, request.document_id)
        
    if doc.status == "error":
        raise HTTPException(status_code=400, detail=f"Cannot review document: {doc.error_message or 'Ingestion failed'}")
        
    # 2. Check for existing completed review unless force_rerun
    if not request.force_rerun:
        existing = get_latest_review(db, request.document_id)
        if existing:
            logger.info("Returning existing review")
            return existing
            
    # 3. Retrieve all clauses for this document
    if not clauses:
        raise HTTPException(status_code=400, detail="No clauses found for this document")
        
    # Convert clauses to dicts for the agents
    clause_dicts = [
        {
            "clause_id": c.clause_id,
            "clause_title": c.clause_title,
            "clause_text": c.clause_text,
            "section": c.section,
            "page_number": c.page_number,
            "position": c.position,
            "clause_type": c.clause_type,
            "word_count": c.word_count
        } for c in clauses
    ]
    
    # 4. Run LangGraph Multi-Agent Workflow
    try:
        workflow_result = run_agentic_review(
            document_id=doc.id,
            document_name=doc.name,
            contract_type=doc.contract_type,
            clauses=clause_dicts
        )
        if "document_name" not in workflow_result or not workflow_result["document_name"]:
            workflow_result["document_name"] = doc.name
    except Exception as e:
        logger.error(f"Review workflow failed: {e}")
        raise HTTPException(status_code=500, detail=f"Agentic review workflow failed: {str(e)}")
        
    # 5. Generate structured report
    import uuid
    review_id = str(uuid.uuid4())
    
    report = generate_review_report(
        review_id=review_id,
        document_id=doc.id,
        workflow_result=workflow_result,
        start_time=start_time
    )
    
    # 6. Save report to DB
    try:
        save_review_report(db, report)
    except Exception as e:
        logger.error(f"Failed to save review to DB: {e}")
        # Return it anyway so user sees results even if DB save failed
        
    return report

@router.get("/{document_id}", response_model=ReviewResponse)
async def get_review(document_id: str, db: Session = Depends(get_db)):
    """Get the latest review for a document."""
    review = get_latest_review(db, document_id)
    if not review:
        raise HTTPException(status_code=404, detail="No review found for this document")
    return review
