"""
Risk Engine — Calculates overall contract risk score with category breakdown.
"""

import logging
from typing import List, Dict, Any

from app.schemas import RiskItem, MissingClauseItem

logger = logging.getLogger(__name__)

# Canonical risk categories and their display names
CATEGORY_GROUPS = {
    "Confidentiality": ["confidentiality", "nda", "disclosure", "proprietary", "trade secret"],
    "Liability": ["liability", "indemnif", "damages", "loss", "uncapped"],
    "Termination": ["terminat", "exit", "notice period", "cancell"],
    "Payment": ["payment", "invoice", "fee", "compensat", "price", "cost"],
    "Intellectual Property": ["ip", "intellectual property", "ownership", "copyright", "patent"],
    "Governing Law": ["governing law", "jurisdiction", "dispute", "arbitrat"],
    "General": [],
}


def _classify_category(category_str: str) -> str:
    """Map a raw category string from LLM to a canonical group."""
    lower = category_str.lower()
    for canonical, keywords in CATEGORY_GROUPS.items():
        if canonical.lower() in lower:
            return canonical
        for kw in keywords:
            if kw in lower:
                return canonical
    return "General"


def calculate_risk_score(
    risks: List[RiskItem],
    missing_clauses: List[MissingClauseItem]
) -> Dict[str, Any]:
    """
    Calculate an overall risk score (0-100), risk level, and category breakdown.
    Lower score is better (0 = no risk, 100 = extreme risk).
    """
    
    # Base severity weights
    WEIGHTS = {
        "CRITICAL": 15.0,
        "HIGH": 8.0,
        "MEDIUM": 3.0,
        "LOW": 1.0,
        "INFO": 0.0,
    }
    
    # Severity mapping for display
    SEV_DISPLAY = {
        "CRITICAL": "Critical",
        "HIGH": "High",
        "MEDIUM": "Medium",
        "LOW": "Low",
        "INFO": "Low",
    }
    
    score = 0.0
    counts = {"CRITICAL": 0, "HIGH": 0, "MEDIUM": 0, "LOW": 0, "INFO": 0}
    
    # Track raw scores per category (0-100 scale per category)
    category_raw: Dict[str, float] = {}
    category_severity: Dict[str, str] = {}

    # Calculate from detected risks
    for risk in risks:
        sev = risk.severity.upper()
        if sev in WEIGHTS:
            score += WEIGHTS[sev]
            counts[sev] += 1
        
        canon = _classify_category(risk.category)
        prev = category_raw.get(canon, 0.0)
        category_raw[canon] = prev + WEIGHTS.get(sev, 0.0)
        
        # Track highest severity per category
        sev_order = ["CRITICAL", "HIGH", "MEDIUM", "LOW", "INFO"]
        cur_sev = category_severity.get(canon, "INFO")
        if sev_order.index(sev) < sev_order.index(cur_sev):
            category_severity[canon] = sev

    # Calculate from missing clauses
    for mc in missing_clauses:
        imp = mc.importance.upper()
        if imp in WEIGHTS:
            score += WEIGHTS[imp] * 0.8
            counts[imp] = counts.get(imp, 0) + 1

    # Cap and compute final score
    final_score = min(100.0, score)

    # Determine overall risk level
    if final_score >= 40.0 or counts["CRITICAL"] > 0:
        level = "CRITICAL"
    elif final_score >= 20.0 or counts["HIGH"] > 1:
        level = "HIGH"
    elif final_score >= 10.0 or counts["HIGH"] > 0 or counts["MEDIUM"] > 2:
        level = "MEDIUM"
    elif final_score > 0.0:
        level = "LOW"
    else:
        level = "MINIMAL"

    # Normalise category scores to 0-100
    max_cat_score = max(category_raw.values()) if category_raw else 1.0
    category_breakdown = []
    for cat, raw_score in sorted(category_raw.items(), key=lambda x: -x[1]):
        pct = min(100, round(raw_score / max(max_cat_score, 1) * 100))
        sev = category_severity.get(cat, "LOW")
        category_breakdown.append({
            "category": cat,
            "score": pct,
            "severity": SEV_DISPLAY.get(sev, "Low"),
        })

    return {
        "score": round(final_score, 1),
        "level": level,
        "counts": counts,
        "category_breakdown": category_breakdown,
    }
