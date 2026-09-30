"""Document model — represents an uploaded contract."""

import uuid
from datetime import datetime
from sqlalchemy import Column, String, Integer, DateTime, Boolean, Text, Float
from sqlalchemy.orm import relationship
from app.database import Base


class Document(Base):
    __tablename__ = "documents"

    id = Column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    name = Column(String(500), nullable=False)
    original_filename = Column(String(500), nullable=False)
    file_path = Column(String(1000), nullable=False)
    file_size = Column(Integer, nullable=False)
    mime_type = Column(String(100))
    extension = Column(String(20))
    page_count = Column(Integer, default=0)
    word_count = Column(Integer, default=0)
    clause_count = Column(Integer, default=0)
    contract_type = Column(String(100))          # NDA, Employment, Vendor, etc.
    status = Column(String(50), default="uploaded")  # uploaded|processing|indexed|reviewed|error
    ocr_used = Column(Boolean, default=False)
    ocr_confidence = Column(Float)
    processing_time = Column(Float)              # seconds
    error_message = Column(Text)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    # Relationships
    clauses = relationship("Clause", back_populates="document", cascade="all, delete-orphan")
    reviews = relationship("Review", back_populates="document", cascade="all, delete-orphan")
    queries = relationship("Query", back_populates="document", cascade="all, delete-orphan")
