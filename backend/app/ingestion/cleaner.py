"""
Text Cleaner — Normalize and clean extracted contract text.
Preserves legal structure while removing artifacts.
"""

import re
import logging
from typing import Optional

logger = logging.getLogger(__name__)

# Unicode normalization replacements
UNICODE_REPLACEMENTS = {
    "\u2013": "-",      # en dash
    "\u2014": "--",     # em dash
    "\u2018": "'",      # left single quote
    "\u2019": "'",      # right single quote
    "\u201c": '"',      # left double quote
    "\u201d": '"',      # right double quote
    "\u2022": "*",      # bullet
    "\u2026": "...",    # ellipsis
    "\u00a0": " ",      # non-breaking space
    "\u00ad": "",       # soft hyphen
    "\ufffd": "",       # replacement character
    "\x00": "",         # null byte
    "\x0c": "\n",       # form feed → newline
    "\x0b": "\n",       # vertical tab → newline
}

# Patterns to remove
HEADER_FOOTER_PATTERN = re.compile(
    r"^(Page\s+\d+\s+of\s+\d+|CONFIDENTIAL|DRAFT|PRIVATE|www\.\S+\.com)\s*$",
    re.IGNORECASE | re.MULTILINE,
)
EXCESSIVE_WHITESPACE = re.compile(r" {3,}")
EXCESSIVE_NEWLINES = re.compile(r"\n{4,}")


def clean_text(text: str) -> str:
    """
    Clean raw extracted text from PDF/DOCX/OCR.
    Preserves legal structure and formatting cues.
    """
    if not text:
        return ""

    # Unicode normalization
    for char, replacement in UNICODE_REPLACEMENTS.items():
        text = text.replace(char, replacement)

    # Remove header/footer artifacts
    text = HEADER_FOOTER_PATTERN.sub("", text)

    # Fix hyphenated line breaks (common in PDFs)
    text = re.sub(r"(\w)-\n(\w)", r"\1\2", text)

    # Normalize whitespace — but preserve paragraph structure
    lines = text.split("\n")
    cleaned_lines = []
    for line in lines:
        line = EXCESSIVE_WHITESPACE.sub(" ", line)
        line = line.strip()
        cleaned_lines.append(line)

    text = "\n".join(cleaned_lines)

    # Collapse excessive blank lines
    text = EXCESSIVE_NEWLINES.sub("\n\n\n", text)

    # Strip leading/trailing whitespace
    text = text.strip()

    return text


def clean_clause_text(text: str) -> str:
    """
    Clean an individual clause's text.
    More aggressive than document-level cleaning.
    """
    text = clean_text(text)

    # Remove leading clause numbering (keep the text, remove number prefix)
    # e.g., "1.2.3 Confidentiality" → keep as-is (useful for context)

    # Remove trailing reference noise
    text = re.sub(r"\s+\d+\s*$", "", text)

    return text.strip()


def detect_contract_language(text: str) -> str:
    """
    Heuristically detect the primary language of contract text.
    Returns ISO 639-1 code.
    """
    # Simple heuristic: check for common English legal terms
    english_legal_terms = [
        "hereby", "whereas", "hereinafter", "notwithstanding",
        "indemnify", "liability", "termination", "governing law",
        "jurisdiction", "confidential", "agreement", "party",
    ]
    text_lower = text.lower()
    matches = sum(1 for term in english_legal_terms if term in text_lower)
    if matches >= 3:
        return "en"
    return "en"  # Default to English for now


def normalize_section_title(title: str) -> str:
    """Normalize a section/clause title for consistent comparison."""
    # Remove leading numbers/bullets
    title = re.sub(r"^[\d\.\(\)\s]+", "", title)
    title = title.strip()
    # Title case
    return title.title()


def truncate_text(text: str, max_chars: int = 500) -> str:
    """Truncate text to max_chars, ending at a word boundary."""
    if len(text) <= max_chars:
        return text
    truncated = text[:max_chars]
    # Find last space
    last_space = truncated.rfind(" ")
    if last_space > max_chars * 0.7:
        truncated = truncated[:last_space]
    return truncated + "..."
