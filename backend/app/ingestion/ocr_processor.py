"""
OCR Processor — Extract text from scanned PDFs and images using Tesseract.
Automatically detects OCR quality via confidence scores.
"""

import io
import logging
from dataclasses import dataclass, field
from typing import List, Optional, Tuple

logger = logging.getLogger(__name__)


@dataclass
class OCRPageResult:
    page_number: int
    text: str
    confidence: float           # 0-100 average confidence
    word_count: int
    char_count: int


@dataclass
class OCRResult:
    pages: List[OCRPageResult]
    total_pages: int
    average_confidence: float
    full_text: str
    successful: bool
    error: Optional[str] = None


def check_tesseract_available() -> bool:
    """Check if Tesseract OCR is installed and accessible."""
    try:
        import pytesseract
        pytesseract.get_tesseract_version()
        return True
    except Exception:
        return False


def ocr_image_bytes(image_bytes: bytes, page_number: int = 1, lang: str = "eng") -> OCRPageResult:
    """
    Run OCR on a single image (as bytes).
    Returns text with confidence score.
    """
    import pytesseract
    from PIL import Image

    try:
        img = Image.open(io.BytesIO(image_bytes))

        # Get detailed OCR data including confidence
        data = pytesseract.image_to_data(
            img,
            lang=lang,
            output_type=pytesseract.Output.DICT,
            config="--psm 6",  # Assume uniform block of text
        )

        # Extract text and calculate average confidence
        words = []
        confidences = []
        for i, conf in enumerate(data["conf"]):
            if conf != -1:  # -1 means no confidence data
                word = data["text"][i].strip()
                if word:
                    words.append(word)
                    confidences.append(float(conf))

        text = " ".join(words)
        avg_confidence = sum(confidences) / len(confidences) if confidences else 0.0

        return OCRPageResult(
            page_number=page_number,
            text=text,
            confidence=avg_confidence,
            word_count=len(words),
            char_count=len(text),
        )

    except Exception as e:
        logger.error(f"OCR failed for page {page_number}: {e}")
        return OCRPageResult(
            page_number=page_number,
            text="",
            confidence=0.0,
            word_count=0,
            char_count=0,
        )


def ocr_pdf_file(file_path: str, lang: str = "eng", dpi: int = 300) -> OCRResult:
    """
    Run OCR on an entire PDF file.
    Converts each page to image and applies Tesseract OCR.
    """
    try:
        from pdf2image import convert_from_path
        import pytesseract
        from PIL import Image

        # Convert PDF pages to images
        try:
            images = convert_from_path(file_path, dpi=dpi)
        except Exception as e:
            logger.warning(f"pdf2image failed, trying PyMuPDF: {e}")
            images = _pdf_to_images_fitz(file_path, dpi=dpi)

        pages: List[OCRPageResult] = []
        for i, img in enumerate(images):
            page_num = i + 1
            # Convert PIL image to bytes
            buf = io.BytesIO()
            img.save(buf, format="PNG")
            result = ocr_image_bytes(buf.getvalue(), page_number=page_num, lang=lang)
            pages.append(result)

        total_confidence = sum(p.confidence for p in pages)
        avg_confidence = total_confidence / len(pages) if pages else 0.0
        full_text = "\n\n".join(p.text for p in pages if p.text.strip())

        return OCRResult(
            pages=pages,
            total_pages=len(pages),
            average_confidence=avg_confidence,
            full_text=full_text,
            successful=True,
        )

    except Exception as e:
        logger.error(f"PDF OCR failed: {e}")
        return OCRResult(
            pages=[],
            total_pages=0,
            average_confidence=0.0,
            full_text="",
            successful=False,
            error=str(e),
        )


def ocr_image_file(file_path: str, lang: str = "eng") -> OCRResult:
    """Run OCR on a standalone image file (PNG, JPG, TIFF, etc.)."""
    try:
        with open(file_path, "rb") as f:
            image_bytes = f.read()

        result = ocr_image_bytes(image_bytes, page_number=1, lang=lang)

        return OCRResult(
            pages=[result],
            total_pages=1,
            average_confidence=result.confidence,
            full_text=result.text,
            successful=True,
        )
    except Exception as e:
        logger.error(f"Image OCR failed: {e}")
        return OCRResult(
            pages=[],
            total_pages=0,
            average_confidence=0.0,
            full_text="",
            successful=False,
            error=str(e),
        )


def _pdf_to_images_fitz(file_path: str, dpi: int = 300):
    """Fallback: convert PDF pages to PIL images using PyMuPDF."""
    import fitz
    from PIL import Image

    images = []
    doc = fitz.open(file_path)
    zoom = dpi / 72  # 72 is the default DPI for PDF
    mat = fitz.Matrix(zoom, zoom)

    for page_num in range(len(doc)):
        page = doc[page_num]
        pix = page.get_pixmap(matrix=mat)
        img_bytes = pix.tobytes("png")
        img = Image.open(io.BytesIO(img_bytes))
        images.append(img)

    doc.close()
    return images
