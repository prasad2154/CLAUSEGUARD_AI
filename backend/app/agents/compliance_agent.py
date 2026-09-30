"""
Compliance Agent — Checks contract clauses against organizational playbook rules.
Evaluates both deterministic pattern matching and custom playbook rules.
"""

import logging
from typing import List, Dict, Any, Set

from app.schemas import RiskItem
from app.api.playbook import DEFAULT_RULES

logger = logging.getLogger(__name__)


def run_compliance_check(
    clauses: List[Dict[str, Any]],
    contract_type: str,
    indexed_clause_ids: Set[str],
) -> List[RiskItem]:
    """
    Run compliance checks against organizational playbook rules.
    Detects violations and non-standard terms based on playbook rules.
    """
    logger.info(f"Running compliance playbook checks for {contract_type}")
    
    compliance_risks: List[RiskItem] = []
    seen_violations: Set[str] = set()

    for rule in DEFAULT_RULES:
        if not rule.get("enabled", True):
            continue

        applies_to = rule.get("applies_to", ["All"])
        if "All" not in applies_to and contract_type not in applies_to:
            continue

        # If it's a clause-level risk rule
        if not rule.get("missing_indicator", False):
            keywords = [kw.lower() for kw in rule.get("detection_keywords", [])]
            patterns = [p.lower() for p in rule.get("risk_patterns", [])]

            for clause in clauses:
                clause_text = (clause.get("clause_text") or "").lower()
                clause_id = clause.get("clause_id")

                if not clause_text or not clause_id:
                    continue

                matched_keyword = any(kw in clause_text for kw in keywords)
                matched_pattern = any(p in clause_text for p in patterns) if patterns else matched_keyword

                if matched_pattern or (matched_keyword and not patterns):
                    violation_key = f"{rule['name']}::{clause_id}"
                    if violation_key in seen_violations:
                        continue
                    seen_violations.add(violation_key)

                    # Extract the sentence or phrase containing the matched term as evidence
                    evidence = clause.get("clause_text", "")
                    if len(evidence) > 400:
                        evidence = evidence[:400] + "..."

                    compliance_risks.append(RiskItem(
                        title=f"Playbook Violation: {rule['name']}",
                        category=rule.get("category", "Compliance & Legal"),
                        severity=rule.get("severity", "MEDIUM"),
                        clause_id=clause_id,
                        page_number=clause.get("page_number", 1),
                        evidence=evidence,
                        section=clause.get("section") or clause.get("clause_title"),
                        explanation=rule.get("description", "Violates organization playbook standards."),
                        recommendation=rule.get("recommendation", "Review and negotiate terms to align with standard playbook."),
                        confidence=0.95,
                    ))

    logger.info(f"Compliance agent detected {len(compliance_risks)} playbook findings")
    return compliance_risks
