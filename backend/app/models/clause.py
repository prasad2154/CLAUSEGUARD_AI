"""Clause model — a single segmented clause from a document."""

import uuid
from datetime import datetime
from sqlalchemy import Column, String, Integer, DateTime, Text, Float, ForeignKey, JSON
from sqlalchemy.orm import relationship
from app.database import Base


class Clause(Base):
    __tablename__ = "clauses"

    id = Column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    document_id = Column(String(36), ForeignKey("documents.id", ondelete="CASCADE"), nullable=False)
    clause_id = Column(String(50), nullable=False)    # e.g., CLAUSE-005
    clause_title = Column(String(500))
    clause_text = Column(Text, nullable=False)
    section = Column(String(200))                     # Section name/number
    page_number = Column(Integer, default=1)
    position = Column(Integer, default=0)             # Order within document
    clause_type = Column(String(100))                 # confidentiality | liability | etc.
    word_count = Column(Integer, default=0)
    char_count = Column(Integer, default=0)
    qdrant_id = Column(String(50))                    # Qdrant point ID
    embedding_model = Column(String(100))
    clause_metadata = Column(JSON)                    # Extra metadata as JSON
    created_at = Column(DateTime, default=datetime.utcnow)

    # Relationships
    document = relationship("Document", back_populates="clauses")
