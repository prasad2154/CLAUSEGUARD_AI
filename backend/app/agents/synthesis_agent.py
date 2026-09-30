"""
Synthesis Agent — Generates a final executive summary of the review.
"""

import logging
from typing import List, Dict, Any

from app.agents.prompts import SYNTHESIS_PROMPT
from app.agents.llm_client import call_llm_json
from app.schemas import RiskItem, MissingClauseItem

logger = logging.getLogger(__name__)

def run_synthesis(
    document_name: str,
    contract_type: str,
    risks: List[RiskItem],
    missing_clauses: List[MissingClauseItem],
) -> Dict[str, Any]:
    """
    Generate an executive summary and key recommendations based on findings.
    """
    logger.info("Running synthesis agent")

    # Format risk summary
    risk_summary = []
    for r in risks:
        risk_summary.append(f"- [{r.severity}] {r.title} ({r.category})")
    
    if not risk_summary:
        risk_summary_str = "No major risks identified."
    else:
        risk_summary_str = "\n".join(risk_summary)

    # Format missing clauses summary
    missing_summary = []
    for m in missing_clauses:
        missing_summary.append(f"- [{m.importance}] {m.clause_name}: {m.reason}")

    if not missing_summary:
        missing_summary_str = "No expected standard clauses are missing."
    else:
        missing_summary_str = "\n".join(missing_summary)

    prompt = SYNTHESIS_PROMPT.format(
        document_name=document_name,
        contract_type=contract_type,
        risk_summary=risk_summary_str,
        missing_summary=missing_summary_str,
    )

    try:
        result = call_llm_json(prompt)
    except Exception as e:
        logger.error(f"Synthesis LLM call failed: {e}")
        return {
            "summary": "Review completed. Please see detailed findings.",
            "recommendations": ["Review the identified risks carefully."],
        }

    if not result:
        return {
            "summary": "Review completed. Please see detailed findings.",
            "recommendations": [],
        }

    return {
        "summary": result.get("summary", "Review completed."),
        "recommendations": result.get("recommendations", []),
    }
