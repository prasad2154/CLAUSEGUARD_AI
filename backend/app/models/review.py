"""Review model — AI review results for a document."""

import uuid
from datetime import datetime
from sqlalchemy import Column, String, Integer, DateTime, Text, Float, ForeignKey, JSON
from sqlalchemy.orm import relationship
from app.database import Base


class Review(Base):
    __tablename__ = "reviews"

    id = Column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    document_id = Column(String(36), ForeignKey("documents.id", ondelete="CASCADE"), nullable=False)
    contract_type = Column(String(100))
    overall_risk_score = Column(Float, default=0.0)   # 0-100
    risk_level = Column(String(20))                    # LOW | MEDIUM | HIGH | CRITICAL
    summary = Column(Text)
    critical_count = Column(Integer, default=0)
    high_count = Column(Integer, default=0)
    medium_count = Column(Integer, default=0)
    low_count = Column(Integer, default=0)
    missing_clause_count = Column(Integer, default=0)
    recommendations = Column(JSON)                    # List of recommendation strings
    agent_log = Column(JSON)                          # Agent execution log
    processing_time = Column(Float)
    status = Column(String(50), default="completed")  # processing|completed|error
    error_message = Column(Text)
    created_at = Column(DateTime, default=datetime.utcnow)

    # Relationships
    document = relationship("Document", back_populates="reviews")
    risks = relationship("Risk", back_populates="review", cascade="all, delete-orphan")
    missing_clauses = relationship("MissingClause", back_populates="review", cascade="all, delete-orphan")
