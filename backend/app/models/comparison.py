"""
Comparison model — stores contract version comparison results.
"""

import uuid
from datetime import datetime
from sqlalchemy import Column, String, DateTime, Float, JSON
from app.database import Base


class Comparison(Base):
    __tablename__ = "comparisons"

    id = Column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    document_a_id = Column(String(36), nullable=False)
    document_b_id = Column(String(36), nullable=False)
    document_a_name = Column(String(500))
    document_b_name = Column(String(500))
    summary = Column(JSON)            # {added, removed, modified, unchanged, high_risk_changes, total_differences}
    differences = Column(JSON)        # List of ClauseDiff objects
    processing_time = Column(Float)
    created_at = Column(DateTime, default=datetime.utcnow)
