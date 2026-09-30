"""Risk model — individual detected risk finding."""

import uuid
from datetime import datetime
from sqlalchemy import Column, String, Integer, DateTime, Text, Float, ForeignKey, JSON, Boolean
from sqlalchemy.orm import relationship
from app.database import Base


class Risk(Base):
    __tablename__ = "risks"

    id = Column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    review_id = Column(String(36), ForeignKey("reviews.id", ondelete="CASCADE"), nullable=False)
    document_id = Column(String(36), nullable=False)

    # Risk classification
    title = Column(String(500), nullable=False)
    category = Column(String(100))                # Liability | Confidentiality | etc.
    severity = Column(String(20), nullable=False)  # CRITICAL | HIGH | MEDIUM | LOW | INFO

    # Evidence — MUST come from actual contract text
    clause_id = Column(String(50))                 # e.g., CLAUSE-014
    page_number = Column(Integer)
    evidence = Column(Text)                        # Exact supporting clause text
    section = Column(String(200))

    # Analysis
    explanation = Column(Text)
    recommendation = Column(Text)
    confidence = Column(Float, default=0.0)        # 0.0 - 1.0

    # Status
    is_reviewed = Column(Boolean, default=False)
    reviewer_note = Column(Text)

    created_at = Column(DateTime, default=datetime.utcnow)

    # Relationship
    review = relationship("Review", back_populates="risks")


class MissingClause(Base):
    __tablename__ = "missing_clauses"

    id = Column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    review_id = Column(String(36), ForeignKey("reviews.id", ondelete="CASCADE"), nullable=False)
    document_id = Column(String(36), nullable=False)

    clause_name = Column(String(200), nullable=False)
    importance = Column(String(20))               # CRITICAL | HIGH | MEDIUM | LOW
    reason = Column(Text)
    contract_type = Column(String(100))
    recommendation = Column(Text)

    created_at = Column(DateTime, default=datetime.utcnow)

    # Relationship
    review = relationship("Review", back_populates="missing_clauses")
