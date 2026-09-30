"""
Document Service — Handles database operations for documents and clauses.
"""

import os
import uuid
from typing import List, Dict, Any, Optional
from sqlalchemy.orm import Session

from app.models.document import Document
from app.models.clause import Clause
from app.ingestion.pipeline import IngestionResult
from app.config import get_settings

settings = get_settings()

def get_document(db: Session, document_id: str) -> Optional[Document]:
    """Retrieve a document by ID."""
    return db.query(Document).filter(Document.id == document_id).first()


def get_documents(db: Session, skip: int = 0, limit: int = 100) -> List[Document]:
    """List documents with pagination."""
    return db.query(Document).order_by(Document.created_at.desc()).offset(skip).limit(limit).all()


def get_document_count(db: Session) -> int:
    """Get total number of documents."""
    return db.query(Document).count()


def create_document_record(
    db: Session,
    filename: str,
    original_filename: str,
    file_path: str,
    file_size: int,
    document_id: Optional[str] = None
) -> Document:
    """Create a new document record in 'uploaded' state."""
    ext = os.path.splitext(filename)[1].lower().lstrip(".")
    
    doc = Document(
        id=document_id or str(uuid.uuid4()),
        name=original_filename,
        original_filename=original_filename,
        file_path=file_path,
        file_size=file_size,
        extension=ext,
        status="uploaded"
    )
    
    db.add(doc)
    db.commit()
    db.refresh(doc)
    return doc


def update_document_from_ingestion(db: Session, result: IngestionResult) -> Document:
    """Update document record with final ingestion results."""
    doc = get_document(db, result.document_id)
    if not doc:
        raise ValueError(f"Document {result.document_id} not found")
        
    doc.page_count = result.page_count
    doc.word_count = result.word_count
    doc.clause_count = result.clause_count
    doc.contract_type = result.contract_type
    doc.ocr_used = result.ocr_used
    doc.ocr_confidence = result.ocr_confidence
    doc.processing_time = result.processing_time
    
    if result.success:
        doc.status = "indexed"
        doc.error_message = None
    else:
        doc.status = "error"
        doc.error_message = result.error
        
    db.commit()
    db.refresh(doc)
    return doc


def save_clauses(db: Session, result: IngestionResult, qdrant_ids: List[str]) -> None:
    """Save all extracted clauses to the SQL database."""
    if len(result.clauses) != len(qdrant_ids):
        raise ValueError("Number of clauses must match number of Qdrant IDs")
        
    # Clear any previous clauses for this document (e.g. on reprocess)
    db.query(Clause).filter(Clause.document_id == result.document_id).delete()
    db.commit()

    clause_records = []
    
    for clause, q_id in zip(result.clauses, qdrant_ids):
        record = Clause(
            document_id=result.document_id,
            clause_id=clause.clause_id,
            clause_title=clause.clause_title,
            clause_text=clause.clause_text,
            section=clause.section,
            page_number=clause.page_number,
            position=clause.position,
            clause_type=clause.clause_type,
            word_count=clause.word_count,
            char_count=clause.char_count,
            qdrant_id=q_id,
            embedding_model=settings.embedding_model,
        )
        clause_records.append(record)
        
    # Bulk insert
    db.bulk_save_objects(clause_records)
    db.commit()


def delete_document(db: Session, document_id: str) -> bool:
    """Delete a document and clean up files and vector store."""
    doc = get_document(db, document_id)
    if not doc:
        return False
        
    # 1. Delete file
    if doc.file_path and os.path.exists(doc.file_path):
        try:
            os.remove(doc.file_path)
        except OSError:
            pass
            
    # 2. Delete vectors from Qdrant
    from app.retrieval.qdrant_store import delete_document_clauses
    delete_document_clauses(document_id)
    
    # 3. Delete from SQL DB (cascade deletes clauses, reviews, queries)
    db.delete(doc)
    db.commit()
    
    return True


def get_document_clauses(db: Session, document_id: str) -> List[Clause]:
    """Get all SQL clauses for a document."""
    return db.query(Clause).filter(Clause.document_id == document_id).order_by(Clause.position).all()
