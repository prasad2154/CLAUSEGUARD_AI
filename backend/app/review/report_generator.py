"""
Report Generator — Packages review results into a final structured schema.
"""

import time
from typing import Dict, Any

from app.schemas import ReviewResponse
from app.review.risk_engine import calculate_risk_score

def generate_review_report(
    review_id: str,
    document_id: str,
    workflow_result: Dict[str, Any],
    start_time: float,
) -> ReviewResponse:
    """
    Format the LangGraph workflow results into the final ReviewResponse schema.
    """
    risks = workflow_result.get("risks", [])
    missing_clauses = workflow_result.get("missing_clauses", [])
    
    score_data = calculate_risk_score(risks, missing_clauses)
    
    processing_time = time.time() - start_time
    
    return ReviewResponse(
        review_id=review_id,
        document_id=document_id,
        document_name=workflow_result.get("document_name", "Unknown Document"),
        contract_type=workflow_result.get("contract_type", "General Contract"),
        overall_risk_score=score_data["score"],
        risk_level=score_data["level"],
        summary=workflow_result.get("summary", ""),
        critical_count=score_data["counts"]["CRITICAL"],
        high_count=score_data["counts"]["HIGH"],
        medium_count=score_data["counts"]["MEDIUM"],
        low_count=score_data["counts"]["LOW"],
        missing_clause_count=len(missing_clauses),
        risks=risks,
        missing_clauses=missing_clauses,
        recommendations=workflow_result.get("recommendations", []),
        processing_time=processing_time,
        category_breakdown=score_data.get("category_breakdown", []),
    )

