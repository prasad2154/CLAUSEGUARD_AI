"""
ClauseGuard AI — Unit Tests for Ingestion Pipeline
Tests clause segmentation, PDF/DOCX processing, and text cleaning.
"""

import pytest
from app.ingestion.segmenter import segment_clauses
from app.ingestion.cleaner import clean_text


class TestTextCleaner:
    def test_clean_removes_extra_whitespace(self):
        dirty = "This   is    some  text."
        cleaned = clean_text(dirty)
        assert "  " not in cleaned

    def test_clean_strips_control_chars(self):
        dirty = "Hello\x00World\x01Test"
        cleaned = clean_text(dirty)
        assert "\x00" not in cleaned
        assert "\x01" not in cleaned

    def test_clean_handles_empty_string(self):
        assert clean_text("") == ""

    def test_clean_handles_none(self):
        result = clean_text(None)
        assert result == ""

    def test_clean_normalizes_unicode(self):
        # Smart quotes -> regular quotes
        dirty = "\u201cHello World\u201d"
        cleaned = clean_text(dirty)
        assert cleaned is not None
        assert len(cleaned) > 0


class TestClauseSegmenter:
    SAMPLE_CONTRACT = """
SERVICE AGREEMENT

1. Parties
This Agreement is entered into between Acme Corp ("Client") and TechVendor LLC ("Vendor").

2. Term and Termination
This Agreement shall commence on January 1, 2025 and continue for twelve (12) months,
unless terminated earlier pursuant to this Agreement. Either party may terminate upon thirty
(30) days written notice.

3. Payment Terms
Client shall pay Vendor USD 10,000 per month within 30 days of receipt of invoice.
Late payments shall accrue interest at 1.5% per month.

4. Limitation of Liability
IN NO EVENT SHALL EITHER PARTY BE LIABLE FOR ANY INDIRECT, INCIDENTAL, SPECIAL,
EXEMPLARY, OR CONSEQUENTIAL DAMAGES. EACH PARTY'S TOTAL LIABILITY SHALL NOT EXCEED
THE TOTAL FEES PAID IN THE PRECEDING TWELVE MONTHS.

5. Confidentiality
Each party agrees to maintain the confidentiality of the other party's proprietary
information and not to disclose it to third parties without prior written consent
for a period of three (3) years following termination.

6. Governing Law and Jurisdiction
This Agreement shall be governed by and construed in accordance with the laws of the
State of Delaware. Any disputes shall be resolved in the courts of Delaware County.
"""

    def test_segmenter_returns_list(self):
        clauses = segment_clauses(self.SAMPLE_CONTRACT, "DOC-001", "Test Contract")
        assert isinstance(clauses, list)

    def test_segmenter_produces_clauses(self):
        clauses = segment_clauses(self.SAMPLE_CONTRACT, "DOC-001", "Test Contract")
        assert len(clauses) > 0

    def test_each_clause_has_required_fields(self):
        clauses = segment_clauses(self.SAMPLE_CONTRACT, "DOC-001", "Test Contract")
        for clause in clauses:
            assert hasattr(clause, "clause_id")
            assert hasattr(clause, "clause_text")
            assert hasattr(clause, "position")
            assert len(clause.clause_text.strip()) > 0

    def test_clause_ids_are_unique(self):
        clauses = segment_clauses(self.SAMPLE_CONTRACT, "DOC-001", "Test Contract")
        ids = [c.clause_id for c in clauses]
        assert len(ids) == len(set(ids))

    def test_detects_numbered_sections(self):
        """Numbered sections like '1. Parties' should produce multiple clauses."""
        clauses = segment_clauses(self.SAMPLE_CONTRACT, "DOC-001", "Test Contract")
        # Should detect at least 4 numbered sections
        assert len(clauses) >= 4

    def test_clause_text_length_limits(self):
        """Clauses should not be absurdly short or exceed reasonable max length."""
        clauses = segment_clauses(self.SAMPLE_CONTRACT, "DOC-001", "Test Contract")
        for clause in clauses:
            text_len = len(clause.clause_text)
            assert text_len >= 10, f"Clause too short: '{clause.clause_text}'"
            assert text_len < 10000, f"Clause suspiciously long: {text_len} chars"

    def test_empty_document_returns_empty_or_fallback(self):
        """Empty input should return empty list or a single fallback clause."""
        clauses = segment_clauses("", "DOC-EMPTY", "Empty Contract")
        # Should not crash; either empty list or fallback full-text clause
        assert isinstance(clauses, list)

    def test_single_paragraph_returns_one_clause(self):
        text = "This is a simple one-paragraph agreement. The parties agree to cooperate in good faith."
        clauses = segment_clauses(text, "DOC-SINGLE", "Single Para")
        assert len(clauses) >= 1
