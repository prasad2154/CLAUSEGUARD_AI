"""Playbook model — configurable risk detection rules."""

import uuid
from datetime import datetime
from sqlalchemy import Column, String, DateTime, Text, Boolean, JSON, Float
from app.database import Base


class PlaybookRule(Base):
    __tablename__ = "playbook_rules"

    id = Column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    name = Column(String(200), nullable=False, unique=True)
    category = Column(String(100), nullable=False)    # Liability | Confidentiality | etc.
    severity = Column(String(20), nullable=False)     # CRITICAL | HIGH | MEDIUM | LOW
    description = Column(Text)
    detection_keywords = Column(JSON)                 # List of keywords to look for
    risk_patterns = Column(JSON)                      # List of risky patterns
    missing_indicator = Column(Boolean, default=False) # True = flag if MISSING
    enabled = Column(Boolean, default=True)
    applies_to = Column(JSON)                          # List of contract types
    recommendation = Column(Text)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
