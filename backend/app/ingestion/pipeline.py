"""
Ingestion Pipeline — Orchestrates the full document processing workflow.

Pipeline stages:
1. File validation
2. Text extraction (PDF/DOCX/image)
3. OCR if needed
4. Text cleaning
5. Clause segmentation
6. Metadata extraction
7. Embedding generation
8. Vector store insertion
9. Database persistence
"""

import os
import time
import logging
import uuid
from dataclasses import dataclass, field
from typing import List, Optional, Tuple
from pathlib import Path

from app.config import get_settings
from app.ingestion.cleaner import clean_text
from app.ingestion.segmenter import ClauseSegment, segment_clauses, segment_from_docx_paragraphs

logger = logging.getLogger(__name__)
settings = get_settings()


@dataclass
class PipelineStatus:
    """Real-time processing status for UI progress tracking."""
    stage: str
    message: str
    progress: int           # 0-100
    error: Optional[str] = None


@dataclass
class IngestionResult:
    """Final result of the full ingestion pipeline."""
    document_id: str
    document_name: str
    page_count: int
    word_count: int
    clause_count: int
    contract_type: Optional[str]
    ocr_used: bool
    ocr_confidence: Optional[float]
    clauses: List[ClauseSegment]
    processing_time: float
    stages_completed: List[str]
    error: Optional[str] = None
    success: bool = True


SUPPORTED_MIME_TYPES = {
    "application/pdf": "pdf",
    "application/vnd.openxmlformats-officedocument.wordprocessingml.document": "docx",
    "application/msword": "doc",
    "image/png": "png",
    "image/jpeg": "jpg",
    "image/tiff": "tiff",
}


def validate_file(file_path: str, filename: str, file_size: int) -> Optional[str]:
    """
    Validate uploaded file before processing.
    Returns error message if invalid, None if valid.
    """
    # Check file size
    max_size = settings.max_file_size_bytes
    if file_size > max_size:
        return f"File size {file_size / 1024 / 1024:.1f}MB exceeds maximum {settings.max_file_size_mb}MB"

    # Check extension
    ext = Path(filename).suffix.lower().lstrip(".")
    if ext not in settings.allowed_extensions_list:
        return f"File type '.{ext}' is not supported. Allowed: {', '.join(settings.allowed_extensions_list)}"

    # Check file exists
    if not os.path.exists(file_path):
        return "File not found after upload"

    return None


def detect_contract_type(text: str, filename: str) -> str:
    """
    Heuristically classify the contract type from content.
    Returns a contract type string.
    """
    text_lower = text.lower()
    filename_lower = filename.lower()

    contract_types = {
        "NDA": ["non-disclosure", "confidentiality agreement", "nda", "proprietary information"],
        "Employment": ["employment agreement", "offer letter", "employment contract", "employee", "salary", "at-will"],
        "Service Agreement": ["service agreement", "statement of work", "sow", "master services", "professional services"],
        "Vendor Agreement": ["vendor agreement", "supplier agreement", "purchase order", "procurement"],
        "SaaS Agreement": ["software as a service", "saas", "subscription agreement", "software license"],
        "License Agreement": ["license agreement", "licensing", "end user license", "eula"],
        "Partnership Agreement": ["partnership agreement", "joint venture", "collaboration agreement"],
        "Consulting Agreement": ["consulting agreement", "consultant", "independent contractor"],
        "Lease Agreement": ["lease agreement", "rental agreement", "tenancy", "landlord", "tenant"],
        "Loan Agreement": ["loan agreement", "promissory note", "credit agreement", "lender", "borrower"],
    }

    for contract_type, keywords in contract_types.items():
        if any(kw in text_lower or kw in filename_lower for kw in keywords):
            return contract_type

    return "General Contract"


def run_ingestion_pipeline(
    file_path: str,
    filename: str,
    file_size: int,
    document_id: Optional[str] = None,
    status_callback=None,
) -> IngestionResult:
    """
    Run the complete document ingestion pipeline.

    Args:
        file_path: Path to uploaded file
        filename: Original filename
        file_size: File size in bytes
        document_id: Pre-assigned document ID (generated if None)
        status_callback: Optional callable(PipelineStatus) for progress updates

    Returns:
        IngestionResult with all extracted clauses
    """
    start_time = time.time()
    document_id = document_id or str(uuid.uuid4())
    stages_completed: List[str] = []
    ext = Path(filename).suffix.lower().lstrip(".")

    def update_status(stage: str, message: str, progress: int, error: str = None):
        status = PipelineStatus(stage=stage, message=message, progress=progress, error=error)
        logger.info(f"[Pipeline] Stage={stage} Progress={progress}% - {message}")
        if status_callback:
            status_callback(status)

    def fail(message: str) -> IngestionResult:
        return IngestionResult(
            document_id=document_id,
            document_name=filename,
            page_count=0,
            word_count=0,
            clause_count=0,
            contract_type=None,
            ocr_used=False,
            ocr_confidence=None,
            clauses=[],
            processing_time=time.time() - start_time,
            stages_completed=stages_completed,
            error=message,
            success=False,
        )

    # ── Stage 1: Validation ────────────────────────────────────────────────
    update_status("validating", "Validating file...", 5)
    error = validate_file(file_path, filename, file_size)
    if error:
        return fail(error)
    stages_completed.append("validation")

    # ── Stage 2: Text Extraction ───────────────────────────────────────────
    update_status("extracting", "Extracting text...", 15)
    pages_text: List[Tuple[int, str]] = []    # [(page_num, text)]
    page_count = 1
    ocr_used = False
    ocr_confidence = None

    try:
        if ext == "pdf":
            from app.ingestion.pdf_processor import extract_pdf, extract_images_from_pdf
            pdf_result = extract_pdf(file_path, min_text_length=settings.min_text_length_for_ocr_skip)

            if pdf_result.error and not pdf_result.pages:
                return fail(f"Could not extract text from PDF: {pdf_result.error}")

            page_count = pdf_result.total_pages

            # Check if OCR is needed for some/all pages
            if pdf_result.needs_ocr:
                update_status("ocr", f"Running OCR on {len(pdf_result.ocr_pages)} pages...", 30)
                from app.ingestion.ocr_processor import ocr_pdf_file, check_tesseract_available

                if check_tesseract_available():
                    ocr_result = ocr_pdf_file(file_path, lang=settings.tesseract_lang)
                    ocr_used = True
                    ocr_confidence = ocr_result.average_confidence

                    if ocr_result.successful:
                        # Merge OCR results into pages_text
                        for page in ocr_result.pages:
                            # If PDF text extraction got something, prefer it; else use OCR
                            pdf_page = next(
                                (p for p in pdf_result.pages if p.page_number == page.page_number),
                                None,
                            )
                            if pdf_page and len(pdf_page.text) > settings.min_text_length_for_ocr_skip:
                                pages_text.append((page.page_number, clean_text(pdf_page.text)))
                            else:
                                pages_text.append((page.page_number, clean_text(page.text)))
                    else:
                        logger.warning(f"OCR failed, using raw PDF text: {ocr_result.error}")
                        for page in pdf_result.pages:
                            pages_text.append((page.page_number, clean_text(page.text)))
                else:
                    logger.warning("Tesseract not available, using PDF text as-is")
                    for page in pdf_result.pages:
                        pages_text.append((page.page_number, clean_text(page.text)))
            else:
                for page in pdf_result.pages:
                    pages_text.append((page.page_number, clean_text(page.text)))

        elif ext in ("docx", "doc"):
            from app.ingestion.docx_processor import extract_docx
            docx_result = extract_docx(file_path)
            if docx_result.error:
                return fail(f"Could not read DOCX file: {docx_result.error}")
            page_count = docx_result.estimated_pages
            # For DOCX, return as single "page" with structured paragraphs
            pages_text = [(1, clean_text(docx_result.full_text))]

        elif ext in ("png", "jpg", "jpeg", "tiff"):
            update_status("ocr", "Running OCR on image...", 25)
            from app.ingestion.ocr_processor import ocr_image_file, check_tesseract_available
            if not check_tesseract_available():
                return fail("OCR is required for image files but Tesseract is not installed.")
            ocr_result = ocr_image_file(file_path, lang=settings.tesseract_lang)
            if not ocr_result.successful:
                return fail(f"OCR failed: {ocr_result.error}")
            ocr_used = True
            ocr_confidence = ocr_result.average_confidence
            pages_text = [(1, clean_text(ocr_result.full_text))]
            page_count = 1

        else:
            return fail(f"Unsupported file extension: {ext}")

    except Exception as e:
        logger.exception(f"Text extraction failed for {filename}")
        return fail(f"Text extraction failed: {str(e)}")

    stages_completed.append("extraction")

    # Check we got meaningful text
    all_text = " ".join(t for _, t in pages_text)
    if len(all_text.strip()) < 20:
        from app.ingestion.ocr_processor import check_tesseract_available
        if not check_tesseract_available() and ocr_used is False:
            return fail("No readable text found in document. It may be a scanned image and OCR (Tesseract) is not installed on the system.")
        return fail("Could not extract readable text from the document. The file may be corrupt or empty.")

    # ── Stage 3: Clause Segmentation ──────────────────────────────────────
    update_status("segmenting", "Detecting and segmenting clauses...", 50)
    try:
        if ext in ("docx", "doc"):
            from app.ingestion.docx_processor import extract_docx
            from app.ingestion.segmenter import segment_from_docx_paragraphs
            docx_result = extract_docx(file_path)
            if docx_result.paragraphs:
                clauses = segment_from_docx_paragraphs(
                    docx_result.paragraphs,
                    min_length=settings.clause_min_length,
                    max_length=settings.clause_max_length,
                )
            else:
                clauses = segment_clauses(
                    pages_text,
                    min_length=settings.clause_min_length,
                    max_length=settings.clause_max_length,
                    document_id=document_id,
                )
        else:
            clauses = segment_clauses(
                pages_text,
                min_length=settings.clause_min_length,
                max_length=settings.clause_max_length,
                document_id=document_id,
            )

        if not clauses:
            # Fallback: split by paragraphs to preserve clause structure
            paragraphs = [p.strip() for p in all_text.split("\n\n") if len(p.strip()) > 15]
            if not paragraphs:
                paragraphs = [all_text.strip()]
            from app.ingestion.segmenter import ClauseSegment
            clauses = []
            for p_idx, para in enumerate(paragraphs[:settings.max_clauses_per_doc]):
                first_line = para.split("\n")[0][:60].strip()
                clauses.append(ClauseSegment(
                    clause_id=f"CLAUSE-{p_idx+1:03d}",
                    clause_title=first_line if len(first_line) > 3 else f"Section {p_idx+1}",
                    clause_text=para[:settings.clause_max_length],
                    section=f"Section {p_idx+1}",
                    page_number=1,
                    position=p_idx,
                    word_count=len(para.split()),
                    char_count=len(para),
                    clause_type=None,
                ))

        # Limit to max clauses
        clauses = clauses[:settings.max_clauses_per_doc]

    except Exception as e:
        logger.exception("Clause segmentation failed")
        return fail(f"Clause segmentation failed: {str(e)}")

    stages_completed.append("segmentation")

    # ── Stage 4: Contract Type Detection ─────────────────────────────────
    update_status("classifying", "Classifying contract type...", 65)
    contract_type = detect_contract_type(all_text, filename)
    stages_completed.append("classification")

    # ── Stage 5: Word Count ────────────────────────────────────────────────
    word_count = len(all_text.split())

    # Done
    processing_time = time.time() - start_time
    update_status("complete", f"Processed {len(clauses)} clauses", 100)

    return IngestionResult(
        document_id=document_id,
        document_name=filename,
        page_count=page_count,
        word_count=word_count,
        clause_count=len(clauses),
        contract_type=contract_type,
        ocr_used=ocr_used,
        ocr_confidence=ocr_confidence,
        clauses=clauses,
        processing_time=processing_time,
        stages_completed=stages_completed,
        success=True,
    )
