"""
Playbook API — Manage organizational contract review rules and risk patterns.
"""

import uuid
from typing import List, Optional
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from pydantic import BaseModel

from app.database import get_db
from app.models.playbook import PlaybookRule
from app.schemas import PlaybookRuleResponse, PlaybookRuleUpdate

router = APIRouter(prefix="/api/playbook", tags=["Playbook"])

DEFAULT_RULES = [
    {
        "name": "Uncapped Liability",
        "category": "Liability & Damages",
        "severity": "CRITICAL",
        "description": "Contracts with unlimited or uncapped liability expose the organization to catastrophic financial loss.",
        "detection_keywords": ["unlimited liability", "no cap on liability", "without limitation", "unlimited damages"],
        "risk_patterns": ["liable for any and all", "shall not be subject to any limitation of liability"],
        "missing_indicator": False,
        "enabled": True,
        "applies_to": ["All", "MSA", "SaaS", "Vendor Agreement"],
        "recommendation": "Cap total liability to fees paid in the previous 12 months, or a mutually agreed fixed ceiling."
    },
    {
        "name": "Broad Asymmetric Indemnification",
        "category": "Indemnification",
        "severity": "HIGH",
        "description": "One-way indemnity clauses forcing our party to defend and hold harmless the counterparty for broad indirect losses.",
        "detection_keywords": ["indemnify", "defend and hold harmless", "gross negligence", "consequential loss"],
        "risk_patterns": ["indemnify and hold harmless against any loss", "including reasonable attorney fees"],
        "missing_indicator": False,
        "enabled": True,
        "applies_to": ["All", "NDA", "MSA"],
        "recommendation": "Limit indemnity strictly to third-party direct claims arising from gross negligence or willful misconduct."
    },
    {
        "name": "Missing Governing Law & Jurisdiction",
        "category": "Compliance & Legal",
        "severity": "HIGH",
        "description": "Absence of an explicit choice of law and venue clause creates severe jurisdictional ambiguity in disputes.",
        "detection_keywords": ["governing law", "jurisdiction", "venue", "laws of the state"],
        "risk_patterns": [],
        "missing_indicator": True,
        "enabled": True,
        "applies_to": ["All"],
        "recommendation": "Insert a clear governing law and exclusive jurisdiction clause designating acceptable courts."
    },
    {
        "name": "Missing Data Protection & Privacy Clause",
        "category": "Data Security & IP",
        "severity": "HIGH",
        "description": "Contracts involving data transfer must contain mandatory GDPR/CCPA security compliance obligations.",
        "detection_keywords": ["data protection", "gdpr", "personal data", "security measures", "data breach"],
        "risk_patterns": [],
        "missing_indicator": True,
        "enabled": True,
        "applies_to": ["SaaS", "Vendor Agreement", "DPA"],
        "recommendation": "Append standard Data Protection Addendum (DPA) specifying 72-hour breach notice and strict audit rights."
    },
    {
        "name": "Perpetual Confidentiality Obligation",
        "category": "Confidentiality",
        "severity": "MEDIUM",
        "description": "Indefinite or perpetual confidentiality terms for standard commercial disclosures.",
        "detection_keywords": ["in perpetuity", "perpetual obligation", "survive indefinitely", "without time limitation"],
        "risk_patterns": ["shall survive indefinitely", "perpetual confidentiality"],
        "missing_indicator": False,
        "enabled": True,
        "applies_to": ["NDA", "MSA"],
        "recommendation": "Limit confidentiality obligations to 3 to 5 years following termination, except for trade secrets."
    },
    {
        "name": "Unilateral Termination for Convenience",
        "category": "Termination",
        "severity": "MEDIUM",
        "description": "Clause allows only the counterparty to terminate at will without cause on short notice.",
        "detection_keywords": ["terminate for convenience", "at any time without cause", "sole discretion"],
        "risk_patterns": ["customer may terminate at any time upon notice", "at its sole option and convenience"],
        "missing_indicator": False,
        "enabled": True,
        "applies_to": ["All"],
        "recommendation": "Make termination for convenience mutual with at least 30-60 days advance written notice."
    }
]


def seed_default_rules(db: Session):
    count = db.query(PlaybookRule).count()
    if count == 0:
        for r in DEFAULT_RULES:
            rule = PlaybookRule(
                id=str(uuid.uuid4()),
                name=r["name"],
                category=r["category"],
                severity=r["severity"],
                description=r["description"],
                detection_keywords=r["detection_keywords"],
                risk_patterns=r["risk_patterns"],
                missing_indicator=r["missing_indicator"],
                enabled=r["enabled"],
                applies_to=r["applies_to"],
                recommendation=r["recommendation"]
            )
            db.add(rule)
        db.commit()


@router.get("", response_model=List[PlaybookRuleResponse])
async def list_rules(db: Session = Depends(get_db)):
    """List all playbook risk rules."""
    seed_default_rules(db)
    return db.query(PlaybookRule).order_by(PlaybookRule.category, PlaybookRule.name).all()


class CreateRuleRequest(BaseModel):
    name: str
    category: str
    severity: str
    description: Optional[str] = None
    detection_keywords: Optional[List[str]] = []
    risk_patterns: Optional[List[str]] = []
    missing_indicator: bool = False
    enabled: bool = True
    applies_to: Optional[List[str]] = ["All"]
    recommendation: Optional[str] = None


@router.post("", response_model=PlaybookRuleResponse)
async def create_rule(req: CreateRuleRequest, db: Session = Depends(get_db)):
    """Create a new playbook rule."""
    existing = db.query(PlaybookRule).filter(PlaybookRule.name == req.name).first()
    if existing:
        raise HTTPException(status_code=400, detail="Rule with this name already exists")
        
    rule = PlaybookRule(
        id=str(uuid.uuid4()),
        name=req.name,
        category=req.category,
        severity=req.severity,
        description=req.description,
        detection_keywords=req.detection_keywords,
        risk_patterns=req.risk_patterns,
        missing_indicator=req.missing_indicator,
        enabled=req.enabled,
        applies_to=req.applies_to,
        recommendation=req.recommendation
    )
    db.add(rule)
    db.commit()
    db.refresh(rule)
    return rule


@router.put("/{rule_id}", response_model=PlaybookRuleResponse)
async def update_rule(rule_id: str, req: PlaybookRuleUpdate, db: Session = Depends(get_db)):
    """Update or toggle a playbook rule."""
    rule = db.query(PlaybookRule).filter(PlaybookRule.id == rule_id).first()
    if not rule:
        raise HTTPException(status_code=404, detail="Rule not found")
        
    if req.severity is not None:
        rule.severity = req.severity
    if req.description is not None:
        rule.description = req.description
    if req.enabled is not None:
        rule.enabled = req.enabled
    if req.recommendation is not None:
        rule.recommendation = req.recommendation
        
    db.commit()
    db.refresh(rule)
    return rule


@router.delete("/{rule_id}")
async def delete_rule(rule_id: str, db: Session = Depends(get_db)):
    """Delete a custom playbook rule."""
    rule = db.query(PlaybookRule).filter(PlaybookRule.id == rule_id).first()
    if not rule:
        raise HTTPException(status_code=404, detail="Rule not found")
    db.delete(rule)
    db.commit()
    return {"status": "success", "message": "Rule removed"}
