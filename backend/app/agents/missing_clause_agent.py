"""
Missing Clause Agent + Configurable Playbook.
Detects standard clauses expected for each contract type that are absent.
"""

import logging
from typing import List, Dict, Any, Optional

from app.agents.prompts import MISSING_CLAUSE_PROMPT
from app.agents.llm_client import call_llm_json
from app.schemas import MissingClauseItem

logger = logging.getLogger(__name__)

# ────────────────────────────────────────────────────────────────────────────
# Expected clause playbooks per contract type
# ────────────────────────────────────────────────────────────────────────────

EXPECTED_CLAUSES: Dict[str, List[Dict[str, str]]] = {
    "NDA": [
        {"name": "Definition of Confidential Information", "importance": "CRITICAL"},
        {"name": "Confidentiality Obligations", "importance": "CRITICAL"},
        {"name": "Exceptions to Confidentiality", "importance": "HIGH"},
        {"name": "Term and Duration", "importance": "HIGH"},
        {"name": "Return or Destruction of Information", "importance": "MEDIUM"},
        {"name": "Governing Law", "importance": "HIGH"},
        {"name": "Dispute Resolution", "importance": "MEDIUM"},
        {"name": "Permitted Disclosures", "importance": "MEDIUM"},
        {"name": "Remedies for Breach", "importance": "HIGH"},
    ],
    "Employment Agreement": [
        {"name": "Compensation and Salary", "importance": "CRITICAL"},
        {"name": "Job Title and Responsibilities", "importance": "HIGH"},
        {"name": "Term of Employment", "importance": "HIGH"},
        {"name": "Termination Conditions", "importance": "CRITICAL"},
        {"name": "Confidentiality Obligations", "importance": "HIGH"},
        {"name": "Intellectual Property Assignment", "importance": "HIGH"},
        {"name": "Non-Solicitation", "importance": "MEDIUM"},
        {"name": "Benefits", "importance": "MEDIUM"},
        {"name": "Governing Law", "importance": "HIGH"},
        {"name": "At-Will Employment / Notice Period", "importance": "HIGH"},
    ],
    "Service Agreement": [
        {"name": "Scope of Services", "importance": "CRITICAL"},
        {"name": "Payment Terms", "importance": "CRITICAL"},
        {"name": "Delivery / Completion Timeline", "importance": "HIGH"},
        {"name": "Acceptance Criteria", "importance": "HIGH"},
        {"name": "Limitation of Liability", "importance": "CRITICAL"},
        {"name": "Confidentiality", "importance": "HIGH"},
        {"name": "Intellectual Property Ownership", "importance": "HIGH"},
        {"name": "Termination Rights", "importance": "HIGH"},
        {"name": "Warranty", "importance": "MEDIUM"},
        {"name": "Indemnification", "importance": "HIGH"},
        {"name": "Governing Law", "importance": "HIGH"},
        {"name": "Dispute Resolution", "importance": "MEDIUM"},
    ],
    "Vendor Agreement": [
        {"name": "Goods/Services Description", "importance": "CRITICAL"},
        {"name": "Pricing and Payment", "importance": "CRITICAL"},
        {"name": "Delivery Terms", "importance": "HIGH"},
        {"name": "Warranties", "importance": "HIGH"},
        {"name": "Limitation of Liability", "importance": "CRITICAL"},
        {"name": "Indemnification", "importance": "HIGH"},
        {"name": "Confidentiality", "importance": "HIGH"},
        {"name": "Termination", "importance": "HIGH"},
        {"name": "Insurance Requirements", "importance": "MEDIUM"},
        {"name": "Audit Rights", "importance": "LOW"},
        {"name": "Governing Law", "importance": "HIGH"},
    ],
    "SaaS Agreement": [
        {"name": "License Grant", "importance": "CRITICAL"},
        {"name": "Subscription Fees", "importance": "CRITICAL"},
        {"name": "Data Privacy and Security", "importance": "CRITICAL"},
        {"name": "Service Level Agreement (SLA)", "importance": "HIGH"},
        {"name": "Acceptable Use Policy", "importance": "HIGH"},
        {"name": "Limitation of Liability", "importance": "CRITICAL"},
        {"name": "Intellectual Property Ownership", "importance": "HIGH"},
        {"name": "Data Ownership and Portability", "importance": "HIGH"},
        {"name": "Termination and Data Return", "importance": "HIGH"},
        {"name": "Auto-Renewal Terms", "importance": "MEDIUM"},
        {"name": "Governing Law", "importance": "HIGH"},
    ],
    "General Contract": [
        {"name": "Definitions", "importance": "MEDIUM"},
        {"name": "Scope of Agreement", "importance": "HIGH"},
        {"name": "Term and Duration", "importance": "HIGH"},
        {"name": "Payment Terms", "importance": "HIGH"},
        {"name": "Confidentiality", "importance": "HIGH"},
        {"name": "Limitation of Liability", "importance": "CRITICAL"},
        {"name": "Indemnification", "importance": "HIGH"},
        {"name": "Termination Rights", "importance": "HIGH"},
        {"name": "Dispute Resolution", "importance": "MEDIUM"},
        {"name": "Governing Law", "importance": "HIGH"},
        {"name": "Entire Agreement", "importance": "MEDIUM"},
        {"name": "Force Majeure", "importance": "MEDIUM"},
    ],
}


def get_expected_clauses(contract_type: str) -> List[Dict[str, str]]:
    """Get the list of expected clauses for a contract type."""
    # Try exact match first
    if contract_type in EXPECTED_CLAUSES:
        return EXPECTED_CLAUSES[contract_type]

    # Try fuzzy match
    ct_lower = contract_type.lower()
    for key in EXPECTED_CLAUSES:
        if key.lower() in ct_lower or ct_lower in key.lower():
            return EXPECTED_CLAUSES[key]

    # Fall back to General Contract
    return EXPECTED_CLAUSES["General Contract"]


def format_expected_clauses(expected: List[Dict[str, str]]) -> str:
    """Format expected clauses for LLM prompt."""
    lines = []
    for clause in expected:
        lines.append(f"- {clause['name']} (Importance: {clause['importance']})")
    return "\n".join(lines)


def run_missing_clause_detection(
    clauses: List[Dict[str, Any]],
    contract_type: str,
) -> List[MissingClauseItem]:
    """
    Detect missing standard clauses for the given contract type.

    Args:
        clauses: All indexed clauses for this document
        contract_type: Contract type string

    Returns:
        List of MissingClauseItem objects
    """
    if not clauses:
        # If no clauses, all expected clauses are missing
        expected = get_expected_clauses(contract_type)
        return [
            MissingClauseItem(
                clause_name=ec["name"],
                importance=ec["importance"],
                reason="No contract content could be analyzed.",
                contract_type=contract_type,
                recommendation=f"Include a {ec['name']} clause.",
            )
            for ec in expected
        ]

    from app.agents.risk_agent import format_clauses_context
    clauses_context = format_clauses_context(clauses)
    expected = get_expected_clauses(contract_type)
    expected_str = format_expected_clauses(expected)

    prompt = MISSING_CLAUSE_PROMPT.format(
        contract_type=contract_type,
        clauses_context=clauses_context,
        expected_clauses=expected_str,
    )

    try:
        result = call_llm_json(prompt)
    except Exception as e:
        logger.warning(f"Missing clause detection LLM call failed, using heuristic: {e}")
        return _heuristic_missing_clauses(clauses, contract_type)

    if not result or "missing_clauses" not in result:
        return _heuristic_missing_clauses(clauses, contract_type)

    missing: List[MissingClauseItem] = []
    for raw in result["missing_clauses"]:
        importance = raw.get("importance", "MEDIUM").upper()
        if importance not in {"CRITICAL", "HIGH", "MEDIUM", "LOW"}:
            importance = "MEDIUM"

        missing.append(MissingClauseItem(
            clause_name=raw.get("clause_name", "Unknown"),
            importance=importance,
            reason=raw.get("reason", ""),
            contract_type=contract_type,
            recommendation=raw.get("recommendation", "Consult a legal professional."),
        ))

    logger.info(f"Missing clause detection found {len(missing)} missing clauses")
    return missing if missing else _heuristic_missing_clauses(clauses, contract_type)


def _heuristic_missing_clauses(clauses: List[Dict[str, Any]], contract_type: str) -> List[MissingClauseItem]:
    """Fallback heuristic check against expected clause patterns."""
    expected = get_expected_clauses(contract_type)
    all_text = " ".join(
        (c.get("clause_text") or "") + " " + (c.get("clause_title") or "") + " " + (c.get("section") or "")
        for c in clauses
    ).lower()

    missing: List[MissingClauseItem] = []
    for ec in expected:
        name = ec["name"]
        keywords = [k.lower() for k in name.replace("/", " ").replace("-", " ").split() if len(k) > 3]
        found = any(k in all_text for k in keywords)
        if not found:
            missing.append(MissingClauseItem(
                clause_name=name,
                importance=ec["importance"],
                reason=f"Standard {name} terms were not detected across analyzed contract clauses.",
                contract_type=contract_type,
                recommendation=f"Add a dedicated {name} clause to protect against ambiguity or omitted rights.",
            ))

    return missing

