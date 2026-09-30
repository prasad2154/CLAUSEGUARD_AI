"""
Comparison API — Endpoints for comparing contract versions.
"""

import uuid
import logging
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from app.database import get_db
from app.schemas import CompareRequest, CompareResponse
from app.services.document_service import get_document, get_document_clauses
from app.services.review_service import save_comparison
from app.comparison.contract_compare import compare_contracts

logger = logging.getLogger(__name__)
router = APIRouter(prefix="/api/compare", tags=["Comparison"])

@router.post("", response_model=CompareResponse)
async def compare_documents(
    request: CompareRequest,
    db: Session = Depends(get_db)
):
    """
    Compare two indexed documents and highlight material changes.
    """
    logger.info(f"Comparing doc {request.document_a_id} to {request.document_b_id}")
    
    doc_a = get_document(db, request.document_a_id)
    doc_b = get_document(db, request.document_b_id)
    
    if not doc_a or not doc_b:
        raise HTTPException(status_code=404, detail="One or both documents not found")
        
    clauses_a = get_document_clauses(db, request.document_a_id)
    clauses_b = get_document_clauses(db, request.document_b_id)
    
    if not clauses_a or not clauses_b:
        raise HTTPException(status_code=400, detail="One or both documents have no extracted clauses")

    # Convert to dicts
    dict_a = [c.__dict__ for c in clauses_a]
    dict_b = [c.__dict__ for c in clauses_b]
    
    comparison_id = str(uuid.uuid4())
    
    try:
        response = compare_contracts(
            doc_a_id=request.document_a_id,
            doc_a_name=doc_a.name,
            clauses_a=dict_a,
            doc_b_id=request.document_b_id,
            doc_b_name=doc_b.name,
            clauses_b=dict_b,
            comparison_id=comparison_id
        )
    except Exception as e:
        logger.error(f"Comparison failed: {e}")
        raise HTTPException(status_code=500, detail="Comparison engine failed")
        
    try:
        save_comparison(db, response)
    except Exception as e:
        logger.error(f"Failed to save comparison to DB: {e}")
        
    return response
