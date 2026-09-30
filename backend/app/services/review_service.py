"""
Review Service — Handles database operations for reviews, risks, and Q&A.
"""

import uuid
from typing import List, Dict, Any, Optional
from sqlalchemy.orm import Session
from sqlalchemy import desc

from app.models.document import Document
from app.models.review import Review
from app.models.risk import Risk, MissingClause
from app.models.query import Query, Comparison
from app.schemas import ReviewResponse, QueryResponse, CompareResponse

def save_review_report(db: Session, report: ReviewResponse) -> Review:
    """Save the final review report and its associated risks to the database."""
    
    review = Review(
        id=report.review_id,
        document_id=report.document_id,
        contract_type=report.contract_type,
        overall_risk_score=report.overall_risk_score,
        risk_level=report.risk_level,
        summary=report.summary,
        critical_count=report.critical_count,
        high_count=report.high_count,
        medium_count=report.medium_count,
        low_count=report.low_count,
        missing_clause_count=report.missing_clause_count,
        recommendations=report.recommendations,
        processing_time=report.processing_time,
        status="completed"
    )
    db.add(review)
    db.flush()  # To get review.id
    
    # Save Risks
    risk_records = []
    for r in report.risks:
        risk_records.append(Risk(
            review_id=review.id,
            document_id=report.document_id,
            title=r.title,
            category=r.category,
            severity=r.severity,
            clause_id=r.clause_id,
            page_number=r.page_number,
            evidence=r.evidence,
            section=r.section,
            explanation=r.explanation,
            recommendation=r.recommendation,
            confidence=r.confidence,
        ))
    if risk_records:
        db.bulk_save_objects(risk_records)
        
    # Save Missing Clauses
    missing_records = []
    for m in report.missing_clauses:
        missing_records.append(MissingClause(
            review_id=review.id,
            document_id=report.document_id,
            clause_name=m.clause_name,
            importance=m.importance,
            reason=m.reason,
            contract_type=m.contract_type,
            recommendation=m.recommendation,
        ))
    if missing_records:
        db.bulk_save_objects(missing_records)
        
    # Update document status
    doc = db.query(Document).filter(Document.id == report.document_id).first()
    if doc:
        doc.status = "reviewed"
        
    db.commit()
    return review


def get_latest_review(db: Session, document_id: str) -> Optional[ReviewResponse]:
    """Get the most recent review for a document."""
    review = db.query(Review).filter(
        Review.document_id == document_id,
        Review.status == "completed"
    ).order_by(desc(Review.created_at)).first()
    
    if not review:
        return None
        
    doc = db.query(Document).filter(Document.id == document_id).first()
    doc_name = doc.name if doc else "Unknown Document"
    
    # Reconstruct ReviewResponse schema
    from app.schemas import RiskItem, MissingClauseItem
    
    risks = [
        RiskItem(
            id=r.id,
            title=r.title,
            category=r.category,
            severity=r.severity,
            clause_id=r.clause_id,
            page_number=r.page_number,
            evidence=r.evidence,
            section=r.section,
            explanation=r.explanation,
            recommendation=r.recommendation,
            confidence=r.confidence,
            is_reviewed=r.is_reviewed
        ) for r in review.risks
    ]
    
    missing_clauses = [
        MissingClauseItem(
            id=m.id,
            clause_name=m.clause_name,
            importance=m.importance,
            reason=m.reason,
            contract_type=m.contract_type,
            recommendation=m.recommendation,
        ) for m in review.missing_clauses
    ]
    
    return ReviewResponse(
        review_id=review.id,
        document_id=review.document_id,
        document_name=doc_name,
        contract_type=review.contract_type,
        overall_risk_score=review.overall_risk_score,
        risk_level=review.risk_level,
        summary=review.summary,
        critical_count=review.critical_count,
        high_count=review.high_count,
        medium_count=review.medium_count,
        low_count=review.low_count,
        missing_clause_count=review.missing_clause_count,
        risks=risks,
        missing_clauses=missing_clauses,
        recommendations=review.recommendations or [],
        processing_time=review.processing_time or 0.0
    )


def save_query(db: Session, document_id: str, query_response: QueryResponse) -> Query:
    """Save a Q&A interaction to history."""
    q = Query(
        id=query_response.query_id,
        document_id=document_id,
        question=query_response.question,
        answer=query_response.answer,
        citations=[c.model_dump() for c in query_response.citations],
        confidence=query_response.confidence,
        has_evidence=query_response.has_evidence,
        retrieval_time=query_response.retrieval_time,
        generation_time=query_response.generation_time
    )
    db.add(q)
    db.commit()
    db.refresh(q)
    return q


def save_comparison(db: Session, compare_response: CompareResponse) -> Comparison:
    """Save a contract comparison result."""
    comp = Comparison(
        id=compare_response.comparison_id,
        document_a_id=compare_response.document_a_id,
        document_b_id=compare_response.document_b_id,
        document_a_name=compare_response.document_a_name,
        document_b_name=compare_response.document_b_name,
        summary=compare_response.summary,
        differences=[d.model_dump() for d in compare_response.differences],
        processing_time=compare_response.processing_time
    )
    db.add(comp)
    db.commit()
    db.refresh(comp)
    return comp
