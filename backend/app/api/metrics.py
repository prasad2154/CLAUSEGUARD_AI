"""
Metrics API — Aggregated analytics and reporting statistics.
"""

from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session
from sqlalchemy import func

from app.database import get_db
from app.models.document import Document
from app.models.review import Review
from app.models.risk import Risk
from app.models.query import Query
from app.models.comparison import Comparison
from app.schemas import MetricsResponse

router = APIRouter(prefix="/api/metrics", tags=["Metrics"])


@router.get("", response_model=MetricsResponse)
async def get_metrics(db: Session = Depends(get_db)):
    """Return live system analytics and risk distributions."""
    total_docs = db.query(Document).count()
    total_revs = db.query(Review).count()
    total_queries = db.query(Query).count()
    total_comparisons = db.query(Comparison).count()
    
    total_risks = db.query(Risk).count()
    critical_risks = db.query(Risk).filter(Risk.severity == "CRITICAL").count()
    high_risks = db.query(Risk).filter(Risk.severity == "HIGH").count()
    
    avg_risk_res = db.query(func.avg(Review.overall_risk_score)).scalar()
    avg_risk_score = round(float(avg_risk_res), 1) if avg_risk_res is not None else 0.0
    
    avg_proc_res = db.query(func.avg(Document.processing_time)).scalar()
    avg_proc_time = round(float(avg_proc_res), 2) if avg_proc_res is not None else 0.0
    
    # Documents by type
    type_counts = db.query(Document.contract_type, func.count(Document.id)).group_by(Document.contract_type).all()
    documents_by_type = {t or "Unknown": c for t, c in type_counts}
    
    # Risks by category
    cat_counts = db.query(Risk.category, func.count(Risk.id)).group_by(Risk.category).all()
    risks_by_category = {c or "General": cnt for c, cnt in cat_counts}
    
    return MetricsResponse(
        total_documents=total_docs,
        total_reviews=total_revs,
        total_queries=total_queries,
        total_comparisons=total_comparisons,
        total_risks_detected=total_risks,
        critical_risks=critical_risks,
        high_risks=high_risks,
        avg_risk_score=avg_risk_score,
        avg_processing_time=avg_proc_time,
        documents_by_type=documents_by_type,
        risks_by_category=risks_by_category
    )
