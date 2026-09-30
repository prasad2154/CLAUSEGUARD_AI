"""
Query API — Endpoints for asking Q&A questions about a contract.
"""

import uuid
import logging
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from app.database import get_db
from app.schemas import QueryRequest, QueryResponse
from app.services.document_service import get_document
from app.services.review_service import save_query
from app.agents.qa_agent import run_qa

logger = logging.getLogger(__name__)
router = APIRouter(prefix="/api/query", tags=["Query"])

@router.post("", response_model=QueryResponse)
async def ask_question(
    request: QueryRequest,
    db: Session = Depends(get_db)
):
    """
    Ask a question about a contract.
    The answer will be grounded in retrieved evidence with citations.
    """
    logger.info(f"Received query for doc {request.document_id}: {request.question}")
    
    # 1. Validate document exists
    doc = get_document(db, request.document_id)
    if not doc:
        raise HTTPException(status_code=404, detail="Document not found")
        
    query_id = str(uuid.uuid4())
    
    # 2. Run Q&A Agent
    response = run_qa(
        question=request.question,
        document_id=request.document_id,
        query_id=query_id
    )
    
    # 3. Save query to DB
    try:
        save_query(db, request.document_id, response)
    except Exception as e:
        logger.error(f"Failed to save query to DB: {e}")
        
    return response
