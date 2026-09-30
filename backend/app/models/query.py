"""Query model — stores Q&A interactions with citations."""

import uuid
from datetime import datetime
from sqlalchemy import Column, String, DateTime, Text, Float, ForeignKey, JSON, Boolean
from sqlalchemy.orm import relationship
from app.database import Base


class Query(Base):
    __tablename__ = "queries"

    id = Column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    document_id = Column(String(36), ForeignKey("documents.id", ondelete="CASCADE"), nullable=False)
    question = Column(Text, nullable=False)
    answer = Column(Text)
    citations = Column(JSON)          # List of {clause_id, page, section, text}
    confidence = Column(Float, default=0.0)
    has_evidence = Column(Boolean, default=False)
    retrieval_time = Column(Float)
    generation_time = Column(Float)
    created_at = Column(DateTime, default=datetime.utcnow)

    # Relationship
    document = relationship("Document", back_populates="queries")


from app.models.comparison import Comparison

__all__ = ["Query", "Comparison"]

