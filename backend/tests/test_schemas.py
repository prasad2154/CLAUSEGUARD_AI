"""
ClauseGuard AI — Schema & Risk Model Unit Tests
"""

import pytest
from pydantic import ValidationError
from app.schemas import (
    RiskItem,
    MissingClauseItem,
    QueryRequest,
    Citation,
    ReviewRequest,
    CompareRequest,
    UploadResponse,
)


class TestRiskItemSchema:
    def test_valid_risk_item(self):
        risk = RiskItem(
            title="Uncapped Liability",
            category="Liability & Damages",
            severity="CRITICAL",
            explanation="No liability cap present in contract.",
            recommendation="Add a liability cap clause.",
            confidence=0.92,
        )
        assert risk.severity == "CRITICAL"
        assert risk.confidence == 0.92

    def test_confidence_must_be_between_0_and_1(self):
        with pytest.raises(ValidationError):
            RiskItem(
                title="Test Risk",
                category="Test",
                severity="HIGH",
                explanation="Test",
                recommendation="Test",
                confidence=1.5,  # Invalid — above 1.0
            )

    def test_confidence_negative_rejected(self):
        with pytest.raises(ValidationError):
            RiskItem(
                title="Test Risk",
                category="Test",
                severity="HIGH",
                explanation="Test",
                recommendation="Test",
                confidence=-0.1,  # Invalid — below 0
            )

    def test_optional_fields_default_none(self):
        risk = RiskItem(
            title="Test",
            category="Test",
            severity="LOW",
            explanation="Test explanation",
            recommendation="Test recommendation",
            confidence=0.5,
        )
        assert risk.clause_id is None
        assert risk.page_number is None
        assert risk.evidence is None


class TestMissingClauseItemSchema:
    def test_valid_missing_clause(self):
        mc = MissingClauseItem(
            clause_name="Governing Law",
            importance="HIGH",
            reason="No governing law clause found.",
            recommendation="Insert: This Agreement shall be governed by the laws of [State].",
        )
        assert mc.clause_name == "Governing Law"
        assert mc.importance == "HIGH"


class TestQueryRequestSchema:
    def test_valid_query(self):
        req = QueryRequest(
            document_id="doc-123",
            question="What is the governing law?"
        )
        assert req.document_id == "doc-123"

    def test_question_too_short(self):
        with pytest.raises(ValidationError):
            QueryRequest(document_id="doc-123", question="ab")  # min_length=3

    def test_question_too_long(self):
        with pytest.raises(ValidationError):
            QueryRequest(document_id="doc-123", question="A" * 2001)  # max_length=2000


class TestCitationSchema:
    def test_valid_citation(self):
        c = Citation(
            clause_id="CLAUSE-007",
            page=3,
            section="3. Payment Terms",
            text="Client shall pay within 30 days of invoice."
        )
        assert c.clause_id == "CLAUSE-007"
        assert c.validate_not_empty() is True

    def test_empty_citation_fails_validation(self):
        c = Citation(
            clause_id="",
            page=0,
            section=None,
            text=""
        )
        assert c.validate_not_empty() is False


class TestReviewRequestSchema:
    def test_valid_review_request(self):
        req = ReviewRequest(document_id="doc-abc-123")
        assert req.document_id == "doc-abc-123"
        assert req.force_rerun is False

    def test_force_rerun_override(self):
        req = ReviewRequest(document_id="doc-abc-123", force_rerun=True)
        assert req.force_rerun is True


class TestCompareRequestSchema:
    def test_valid_compare_request(self):
        req = CompareRequest(
            document_a_id="doc-a-123",
            document_b_id="doc-b-456"
        )
        assert req.document_a_id == "doc-a-123"
        assert req.document_b_id == "doc-b-456"

    def test_missing_document_b_rejected(self):
        with pytest.raises(ValidationError):
            CompareRequest(document_a_id="doc-a-123")  # document_b_id missing


class TestUploadResponseSchema:
    def test_valid_upload_response(self):
        resp = UploadResponse(
            document_id="doc-new-xyz",
            name="Service Agreement v2.pdf",
            status="indexed",
            message="Successfully processed 24 clauses.",
            clause_count=24,
            page_count=8,
            ocr_used=False,
            processing_time=4.31,
        )
        assert resp.clause_count == 24
        assert resp.ocr_used is False
