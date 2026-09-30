"""
Contract Version Comparison — Compares two contracts clause-by-clause.
Detects ADDED, REMOVED, and MODIFIED clauses.
Uses LLM to determine if a modification is a material legal risk, with heuristic fallback.
"""

import logging
import time
import re
from typing import List, Dict, Any

from app.schemas import ClauseDiff, CompareResponse
from app.agents.prompts import COMPARISON_PROMPT
from app.agents.llm_client import call_llm_json

logger = logging.getLogger(__name__)


def _get_clause_key(clause: Dict[str, Any]) -> str:
    """Create a fuzzy matching key for a clause (section or title)."""
    if clause.get("section"):
        return str(clause["section"]).lower().strip()
    if clause.get("clause_title"):
        return str(clause["clause_title"]).lower().strip()
    return clause.get("clause_id", "")


def compare_contracts(
    doc_a_id: str,
    doc_a_name: str,
    clauses_a: List[Dict[str, Any]],
    doc_b_id: str,
    doc_b_name: str,
    clauses_b: List[Dict[str, Any]],
    comparison_id: str
) -> CompareResponse:
    """
    Compare two contract versions and identify material differences.
    """
    logger.info(f"Comparing '{doc_a_name}' vs '{doc_b_name}'")
    start_time = time.time()
    
    # Map clauses by their logical keys
    map_a = {_get_clause_key(c): c for c in clauses_a if _get_clause_key(c)}
    map_b = {_get_clause_key(c): c for c in clauses_b if _get_clause_key(c)}
    
    differences: List[ClauseDiff] = []
    
    # Check for REMOVED and MODIFIED
    for key, clause_a in map_a.items():
        if key not in map_b:
            differences.append(ClauseDiff(
                clause_title=clause_a.get("clause_title") or clause_a.get("section") or "Unknown Clause",
                section=clause_a.get("section"),
                change_type="REMOVED",
                text_a=clause_a.get("clause_text"),
                text_b=None,
                page_a=clause_a.get("page_number"),
                page_b=None,
                risk_impact="MEDIUM",
                risk_explanation="Clause was entirely removed from the new version.",
                severity="MEDIUM"
            ))
        else:
            clause_b = map_b[key]
            text_a = (clause_a.get("clause_text") or "").strip()
            text_b = (clause_b.get("clause_text") or "").strip()
            
            # Simple text identity check first
            if text_a != text_b:
                diff_result = _assess_modification(clause_a, clause_b)
                
                if diff_result["change_type"] == "MODIFIED":
                    differences.append(ClauseDiff(
                        clause_title=clause_b.get("clause_title") or clause_b.get("section") or "Unknown Clause",
                        section=clause_b.get("section"),
                        change_type="MODIFIED",
                        text_a=text_a,
                        text_b=text_b,
                        page_a=clause_a.get("page_number"),
                        page_b=clause_b.get("page_number"),
                        risk_impact=diff_result["risk_impact"],
                        risk_explanation=diff_result["risk_explanation"],
                        severity=diff_result["severity"]
                    ))

    # Check for ADDED
    for key, clause_b in map_b.items():
        if key not in map_a:
            differences.append(ClauseDiff(
                clause_title=clause_b.get("clause_title") or clause_b.get("section") or "Unknown Clause",
                section=clause_b.get("section"),
                change_type="ADDED",
                text_a=None,
                text_b=clause_b.get("clause_text"),
                page_a=None,
                page_b=clause_b.get("page_number"),
                risk_impact="MEDIUM",
                risk_explanation="Clause was added to the new version.",
                severity="MEDIUM"
            ))

    # Generate summary stats
    summary = {
        "added": sum(1 for d in differences if d.change_type == "ADDED"),
        "removed": sum(1 for d in differences if d.change_type == "REMOVED"),
        "modified": sum(1 for d in differences if d.change_type == "MODIFIED"),
        "unchanged": max(0, len(map_b) - sum(1 for d in differences if d.change_type == "MODIFIED") - sum(1 for d in differences if d.change_type == "ADDED")),
        "high_risk_changes": sum(1 for d in differences if d.risk_impact in ("HIGH", "CRITICAL")),
        "total_differences": len(differences),
    }
    
    # Sort differences: High risk first, then by page number
    differences.sort(
        key=lambda x: (0 if x.risk_impact in ("HIGH", "CRITICAL") else 1, x.page_b or x.page_a or 0)
    )

    return CompareResponse(
        comparison_id=comparison_id,
        document_a_id=doc_a_id,
        document_b_id=doc_b_id,
        document_a_name=doc_a_name,
        document_b_name=doc_b_name,
        summary=summary,
        differences=differences,
        processing_time=round(time.time() - start_time, 2)
    )


def _assess_modification(clause_a: Dict[str, Any], clause_b: Dict[str, Any]) -> Dict[str, Any]:
    """Assess if a modification is material and risky via LLM or rule heuristic."""
    text_a = clause_a.get("clause_text", "")
    text_b = clause_b.get("clause_text", "")
    
    if _is_trivial_diff(text_a, text_b):
        return {
            "change_type": "UNCHANGED",
            "is_material": False,
            "risk_impact": "NONE",
            "risk_explanation": None,
            "severity": "NONE"
        }

    prompt = COMPARISON_PROMPT.format(
        clause_id_a=clause_a.get("clause_id", "?"),
        section_a=clause_a.get("section", ""),
        page_a=clause_a.get("page_number", 1),
        text_a=text_a,
        clause_id_b=clause_b.get("clause_id", "?"),
        section_b=clause_b.get("section", ""),
        page_b=clause_b.get("page_number", 1),
        text_b=text_b,
    )
    
    try:
        result = call_llm_json(prompt)
        if result and "change_type" in result:
            return result
    except Exception as e:
        logger.warning(f"Comparison LLM call failed, using heuristic: {e}")
        
    # Heuristic analysis fallback
    high_risk_terms = ["unlimited", "indemnif", "liability", "damages", "breach", "penalty", "sole discretion", "terminate immediately", "governing law"]
    a_lower = text_a.lower()
    b_lower = text_b.lower()
    
    found_high_risk = any(term in b_lower for term in high_risk_terms)
    is_longer_or_shorter = abs(len(text_b) - len(text_a)) > 50

    if found_high_risk and not any(term in a_lower for term in high_risk_terms):
        risk_impact = "HIGH"
        explanation = "New version introduces high-liability risk terms not present in the original clause."
    elif is_longer_or_shorter:
        risk_impact = "MEDIUM"
        explanation = "Substantial textual modification in obligations or scope between drafts."
    else:
        risk_impact = "LOW"
        explanation = "Minor phrasing adjustment between versions."

    return {
        "change_type": "MODIFIED",
        "is_material": risk_impact in ("HIGH", "MEDIUM"),
        "risk_impact": risk_impact,
        "risk_explanation": explanation,
        "severity": risk_impact
    }


def _is_trivial_diff(text_a: str, text_b: str) -> bool:
    """Check if the difference between two texts is purely whitespace or trivial punctuation."""
    a_clean = re.sub(r'\W+', '', text_a.lower())
    b_clean = re.sub(r'\W+', '', text_b.lower())
    return a_clean == b_clean
