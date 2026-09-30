"""
PDF Processor — Extract text from PDF files preserving page numbers.
Uses PyMuPDF (fitz) as primary, pdfplumber as fallback.
Detects whether OCR is needed.
"""

import io
import logging
from dataclasses import dataclass, field
from typing import List, Optional

logger = logging.getLogger(__name__)


@dataclass
class PageContent:
    page_number: int
    text: str
    char_count: int
    needs_ocr: bool = False
    images: List[bytes] = field(default_factory=list)


@dataclass
class PDFExtractionResult:
    pages: List[PageContent]
    total_pages: int
    total_chars: int
    extraction_method: str          # "fitz" | "pdfplumber" | "ocr"
    needs_ocr: bool
    ocr_pages: List[int]
    error: Optional[str] = None

    @property
    def full_text(self) -> str:
        return "\n\n".join(p.text for p in self.pages if p.text.strip())


def extract_pdf(file_path: str, min_text_length: int = 100) -> PDFExtractionResult:
    """
    Extract text from a PDF file page by page.
    Detects if OCR is needed based on text density.
    """
    try:
        return _extract_with_fitz(file_path, min_text_length)
    except Exception as e:
        logger.warning(f"PyMuPDF extraction failed, trying pdfplumber: {e}")
        try:
            return _extract_with_pdfplumber(file_path, min_text_length)
        except Exception as e2:
            logger.error(f"Both PDF extractors failed: {e2}")
            return PDFExtractionResult(
                pages=[],
                total_pages=0,
                total_chars=0,
                extraction_method="failed",
                needs_ocr=True,
                ocr_pages=[],
                error=str(e2),
            )


def _extract_with_fitz(file_path: str, min_text_length: int) -> PDFExtractionResult:
    """Extract using PyMuPDF (fast, preserves structure)."""
    import fitz  # PyMuPDF

    pages: List[PageContent] = []
    ocr_pages: List[int] = []

    doc = fitz.open(file_path)
    total_pages = len(doc)

    for page_num in range(total_pages):
        page = doc[page_num]
        text = page.get_text("text").strip()
        
        # If regular text is short, try blocks
        if len(text) < min_text_length:
            try:
                blocks = page.get_text("blocks")
                block_texts = [b[4].strip() for b in blocks if len(b) > 4 and b[4].strip()]
                combined_blocks = "\n".join(block_texts)
                if len(combined_blocks) > len(text):
                    text = combined_blocks
            except Exception:
                pass

        # Check form fields and annotations
        try:
            widget_texts = []
            for widget in page.widgets():
                if widget.field_value and isinstance(widget.field_value, str):
                    widget_texts.append(widget.field_value.strip())
            if widget_texts:
                text = (text + "\n" + "\n".join(widget_texts)).strip()
        except Exception:
            pass

        char_count = len(text)
        needs_ocr = char_count < min_text_length

        # Extract page images if OCR may be needed
        images = []
        if needs_ocr:
            ocr_pages.append(page_num + 1)
            try:
                pix = page.get_pixmap(dpi=300)
                images = [pix.tobytes("png")]
            except Exception:
                pass

        pages.append(PageContent(
            page_number=page_num + 1,
            text=text,
            char_count=char_count,
            needs_ocr=needs_ocr,
            images=images,
        ))

    doc.close()

    total_chars = sum(p.char_count for p in pages)
    needs_ocr = len(ocr_pages) > 0

    return PDFExtractionResult(
        pages=pages,
        total_pages=total_pages,
        total_chars=total_chars,
        extraction_method="fitz",
        needs_ocr=needs_ocr,
        ocr_pages=ocr_pages,
    )


def _extract_with_pdfplumber(file_path: str, min_text_length: int) -> PDFExtractionResult:
    """Fallback extractor using pdfplumber."""
    import pdfplumber

    pages: List[PageContent] = []
    ocr_pages: List[int] = []

    with pdfplumber.open(file_path) as pdf:
        total_pages = len(pdf.pages)
        for i, page in enumerate(pdf.pages):
            text = page.extract_text() or ""
            text = text.strip()
            char_count = len(text)
            needs_ocr = char_count < min_text_length

            if needs_ocr:
                ocr_pages.append(i + 1)

            pages.append(PageContent(
                page_number=i + 1,
                text=text,
                char_count=char_count,
                needs_ocr=needs_ocr,
            ))

    total_chars = sum(p.char_count for p in pages)

    return PDFExtractionResult(
        pages=pages,
        total_pages=total_pages,
        total_chars=total_chars,
        extraction_method="pdfplumber",
        needs_ocr=len(ocr_pages) > 0,
        ocr_pages=ocr_pages,
    )


def extract_images_from_pdf(file_path: str) -> List[tuple[int, bytes]]:
    """
    Extract page images from PDF for OCR processing.
    Returns list of (page_number, png_bytes) tuples.
    """
    import fitz

    images = []
    try:
        doc = fitz.open(file_path)
        for page_num in range(len(doc)):
            page = doc[page_num]
            pix = page.get_pixmap(dpi=300)
            png_bytes = pix.tobytes("png")
            images.append((page_num + 1, png_bytes))
        doc.close()
    except Exception as e:
        logger.error(f"Failed to extract images from PDF: {e}")

    return images
