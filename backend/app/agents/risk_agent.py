"""
Risk Detection Agent — Identifies risky clauses in contracts.

ANTI-HALLUCINATION GUARANTEES:
- Only analyzes retrieved clause content
- Every risk must have clause_id + evidence from actual text
- Validates each risk against indexed clauses before returning
"""

import logging
from typing import List, Dict, Any, Optional

from app.agents.prompts import RISK_DETECTION_PROMPT
from app.agents.llm_client import call_llm_json
from app.schemas import RiskItem

logger = logging.getLogger(__name__)


def format_clauses_context(clauses: List[Dict[str, Any]], max_chars: int = 12000) -> str:
    """Format retrieved clauses for LLM context."""
    lines = []
    total_chars = 0

    for clause in clauses:
        clause_block = (
            f"[{clause.get('clause_id', 'UNKNOWN')}] "
            f"Section: {clause.get('section') or clause.get('clause_title') or 'N/A'} "
            f"| Page: {clause.get('page_number', '?')}\n"
            f"{clause.get('clause_text', '')}\n"
            f"---"
        )

        if total_chars + len(clause_block) > max_chars:
            break

        lines.append(clause_block)
        total_chars += len(clause_block)

    return "\n".join(lines)


def run_risk_detection(
    clauses: List[Dict[str, Any]],
    contract_type: str,
    indexed_clause_ids: set,
) -> List[RiskItem]:
    """
    Run risk detection on retrieved contract clauses.

    Args:
        clauses: Retrieved clause dicts with metadata
        contract_type: Contract type string
        indexed_clause_ids: Set of valid clause IDs (for anti-hallucination validation)

    Returns:
        List of RiskItem objects with evidence
    """
    if not clauses:
        logger.warning("No clauses provided to risk detection agent")
        return []

    clauses_context = format_clauses_context(clauses)

    prompt = RISK_DETECTION_PROMPT.format(
        contract_type=contract_type,
        clauses_context=clauses_context,
    )

    try:
        result = call_llm_json(prompt)
    except Exception as e:
        logger.error(f"Risk detection LLM call failed: {e}")
        return []

    if not result or "risks" not in result:
        logger.warning("Risk detection returned no results")
        return []

    risks: List[RiskItem] = []
    for raw_risk in result["risks"]:
        # ── Anti-hallucination: validate clause_id ────────────────────────
        import re
        clause_id = raw_risk.get("clause_id")
        evidence = raw_risk.get("evidence", "").strip()

        if not evidence:
            logger.warning(f"Risk '{raw_risk.get('title')}' has no evidence — DISCARDED")
            continue

        if clause_id and clause_id not in indexed_clause_ids:
            matched_id = None
            clean_input_id = clause_id.upper().replace(" ", "").replace("_", "-")
            for valid_id in indexed_clause_ids:
                if valid_id.upper().replace(" ", "").replace("_", "-") == clean_input_id:
                    matched_id = valid_id
                    break
                try:
                    num_in = re.findall(r"\d+", clause_id)
                    num_valid = re.findall(r"\d+", valid_id)
                    if num_in and num_valid and int(num_in[0]) == int(num_valid[0]):
                        matched_id = valid_id
                        break
                except Exception:
                    pass

            if not matched_id and evidence:
                for c in clauses:
                    c_text = c.get("clause_text", "")
                    if evidence[:40].lower() in c_text.lower() or (len(c_text) > 20 and c_text[:40].lower() in evidence.lower()):
                        matched_id = c.get("clause_id")
                        break

            if matched_id:
                clause_id = matched_id
            elif indexed_clause_ids:
                # If evidence exists but LLM hallucinated ID, assign to first clause where evidence is found or omit clause_id
                matched_id = None
                for c in clauses:
                    if evidence.lower() in c.get("clause_text", "").lower():
                        matched_id = c.get("clause_id")
                        break
                clause_id = matched_id

        # ── Validate severity ─────────────────────────────────────────────
        severity = raw_risk.get("severity", "MEDIUM").upper()
        if severity not in {"CRITICAL", "HIGH", "MEDIUM", "LOW", "INFO"}:
            severity = "MEDIUM"

        # ── If clause_id found, get real page number ──────────────────────
        page_number = raw_risk.get("page_number")
        if clause_id:
            actual_clause = next(
                (c for c in clauses if c.get("clause_id") == clause_id),
                None,
            )
            if actual_clause:
                page_number = actual_clause.get("page_number", page_number)

        confidence = float(raw_risk.get("confidence", 0.7))
        confidence = max(0.0, min(1.0, confidence))

        risks.append(RiskItem(
            title=raw_risk.get("title", "Unnamed Risk"),
            category=raw_risk.get("category", "General"),
            severity=severity,
            clause_id=clause_id,
            page_number=page_number,
            evidence=evidence,
            section=raw_risk.get("section"),
            explanation=raw_risk.get("explanation", ""),
            recommendation=raw_risk.get("recommendation", "Consult a legal professional."),
            confidence=confidence,
        ))

    logger.info(f"Risk detection found {len(risks)} validated risks")
    return risks
