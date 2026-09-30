"""
ClauseGuard AI — Pydantic Schemas
All API request/response models with strict validation.
"""

from datetime import datetime
from typing import List, Optional, Dict, Any
from pydantic import BaseModel, Field, ConfigDict


# ────────────────────────────────────────────────────────────────────────────
# Clause Schemas
# ────────────────────────────────────────────────────────────────────────────

class ClauseMetadata(BaseModel):
    document_id: str
    document_name: str
    clause_id: str
    clause_title: Optional[str] = None
    clause_text: str
    section: Optional[str] = None
    page_number: int = 1
    position: int = 0
    clause_type: Optional[str] = None
    document_type: Optional[str] = None


class ClauseResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: str
    document_id: str
    clause_id: str
    clause_title: Optional[str]
    clause_text: str
    section: Optional[str]
    page_number: int
    position: int
    clause_type: Optional[str]
    word_count: int
    created_at: datetime


# ────────────────────────────────────────────────────────────────────────────
# Document Schemas
# ────────────────────────────────────────────────────────────────────────────

class DocumentResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: str
    name: str
    original_filename: str
    file_size: int
    mime_type: Optional[str]
    extension: Optional[str]
    page_count: int
    word_count: int
    clause_count: int
    contract_type: Optional[str]
    status: str
    ocr_used: bool
    ocr_confidence: Optional[float]
    processing_time: Optional[float]
    error_message: Optional[str]
    created_at: datetime
    updated_at: datetime


class DocumentListResponse(BaseModel):
    documents: List[DocumentResponse]
    total: int
    page: int
    page_size: int


class UploadResponse(BaseModel):
    document_id: str
    name: str
    status: str
    message: str
    clause_count: int
    page_count: int
    ocr_used: bool
    processing_time: float


# ────────────────────────────────────────────────────────────────────────────
# Risk Schemas
# ────────────────────────────────────────────────────────────────────────────

class RiskItem(BaseModel):
    """A single detected risk — MUST have evidence from actual contract."""
    id: Optional[str] = None
    title: str
    category: str
    severity: str                     # CRITICAL | HIGH | MEDIUM | LOW | INFO
    clause_id: Optional[str] = None   # e.g., CLAUSE-014
    page_number: Optional[int] = None
    evidence: Optional[str] = None    # Exact supporting clause text
    section: Optional[str] = None
    explanation: str
    recommendation: str
    confidence: float = Field(ge=0.0, le=1.0)
    is_reviewed: bool = False


class MissingClauseItem(BaseModel):
    """A standard clause expected for this contract type that is absent."""
    id: Optional[str] = None
    clause_name: str
    importance: str                   # CRITICAL | HIGH | MEDIUM | LOW
    reason: str
    contract_type: Optional[str] = None
    recommendation: str


# ────────────────────────────────────────────────────────────────────────────
# Review Schemas
# ────────────────────────────────────────────────────────────────────────────

class ReviewRequest(BaseModel):
    document_id: str
    force_rerun: bool = False


class ReviewResponse(BaseModel):
    review_id: str
    document_id: str
    document_name: str
    contract_type: str
    overall_risk_score: float         # 0-100
    risk_level: str                   # LOW | MEDIUM | HIGH | CRITICAL | MINIMAL
    summary: str
    critical_count: int
    high_count: int
    medium_count: int
    low_count: int
    missing_clause_count: int
    risks: List[RiskItem]
    missing_clauses: List[MissingClauseItem]
    recommendations: List[str]
    processing_time: float
    category_breakdown: List[Dict[str, Any]] = Field(default_factory=list)
    """Per-category risk breakdown: [{category, score (0-100), severity}]"""



# ────────────────────────────────────────────────────────────────────────────
# Q&A Schemas
# ────────────────────────────────────────────────────────────────────────────

class Citation(BaseModel):
    """A citation pointing to exact contract content."""
    clause_id: str
    page: int
    section: Optional[str]
    text: str                         # Exact clause text

    def validate_not_empty(self) -> bool:
        return bool(self.clause_id and self.text and self.page > 0)


class QueryRequest(BaseModel):
    document_id: str
    question: str = Field(min_length=3, max_length=2000)


class QueryResponse(BaseModel):
    query_id: str
    question: str
    answer: str
    citations: List[Citation]
    confidence: float = Field(ge=0.0, le=1.0)
    has_evidence: bool
    retrieval_time: float
    generation_time: float


# ────────────────────────────────────────────────────────────────────────────
# Comparison Schemas
# ────────────────────────────────────────────────────────────────────────────

class ClauseDiff(BaseModel):
    """A single clause-level difference between two contract versions."""
    clause_title: str
    section: Optional[str]
    change_type: str                  # ADDED | REMOVED | MODIFIED | UNCHANGED
    text_a: Optional[str]             # Old text
    text_b: Optional[str]             # New text
    page_a: Optional[int]
    page_b: Optional[int]
    risk_impact: Optional[str]        # HIGH | MEDIUM | LOW | NONE
    risk_explanation: Optional[str]
    severity: Optional[str]


class CompareRequest(BaseModel):
    document_a_id: str
    document_b_id: str


class CompareResponse(BaseModel):
    comparison_id: str
    document_a_id: str
    document_b_id: str
    document_a_name: str
    document_b_name: str
    summary: Dict[str, Any]           # {added, removed, modified, unchanged, high_risk_changes}
    differences: List[ClauseDiff]
    processing_time: float


# ────────────────────────────────────────────────────────────────────────────
# Health Schema
# ────────────────────────────────────────────────────────────────────────────

class ServiceStatus(BaseModel):
    name: str
    status: str                       # healthy | degraded | offline
    latency_ms: Optional[float] = None
    details: Optional[str] = None


class HealthResponse(BaseModel):
    status: str                       # healthy | degraded | offline
    version: str
    timestamp: datetime
    services: List[ServiceStatus]


# ────────────────────────────────────────────────────────────────────────────
# Playbook Schemas
# ────────────────────────────────────────────────────────────────────────────

class PlaybookRuleResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: str
    name: str
    category: str
    severity: str
    description: Optional[str]
    detection_keywords: Optional[List[str]]
    risk_patterns: Optional[List[str]]
    missing_indicator: bool
    enabled: bool
    applies_to: Optional[List[str]]
    recommendation: Optional[str]
    created_at: datetime
    updated_at: datetime


class PlaybookRuleUpdate(BaseModel):
    severity: Optional[str] = None
    description: Optional[str] = None
    enabled: Optional[bool] = None
    recommendation: Optional[str] = None


# ────────────────────────────────────────────────────────────────────────────
# Metrics Schema
# ────────────────────────────────────────────────────────────────────────────

class MetricsResponse(BaseModel):
    total_documents: int
    total_reviews: int
    total_queries: int
    total_comparisons: int
    total_risks_detected: int
    critical_risks: int
    high_risks: int
    avg_risk_score: float
    avg_processing_time: float
    documents_by_type: Dict[str, int]
    risks_by_category: Dict[str, int]
