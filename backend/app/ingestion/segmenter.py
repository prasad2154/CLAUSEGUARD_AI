"""
Clause Segmenter — Segment contract text into meaningful legal clauses.

Strategy:
1. Detect numbered sections (1., 1.1, Article 1, Section 1)
2. Detect heading-style clauses (ALL CAPS, Title Case followed by body)
3. Split on structural boundaries
4. Preserve page number context
5. Merge short fragments into their parent section

This is NOT arbitrary chunking — each segment corresponds to a real legal clause.
"""

import re
import logging
from dataclasses import dataclass, field
from typing import List, Optional, Tuple

logger = logging.getLogger(__name__)

# ── Heading patterns that indicate a new clause/section ──────────────────────

# Numbered sections: 1. | 1.1 | 1.1.1 | (1) | A. | I.
NUMBERED_SECTION = re.compile(
    r"^(?:"
    r"\d{1,2}(?:\.\d{1,2}){0,3}\.?\s+"          # 1. | 1.1 | 1.1.1.
    r"|\(\d{1,2}\)\s+"                            # (1)
    r"|[A-Z]{1,3}\.\s+"                           # A. | I.
    r"|Article\s+\d+\b"                           # Article 1
    r"|Section\s+\d+(?:\.\d+)?\b"                 # Section 1 | Section 1.1
    r"|Schedule\s+[A-Z\d]+"                       # Schedule A
    r"|Exhibit\s+[A-Z\d]+"                        # Exhibit A
    r"|Appendix\s+[A-Z\d]+"                       # Appendix A
    r")",
    re.IGNORECASE | re.MULTILINE,
)

# All-caps headings (common in legal documents)
ALL_CAPS_HEADING = re.compile(
    r"^[A-Z][A-Z\s\-\/]{4,60}[A-Z]$"
)

# Title Case headings (4+ words or fewer but clearly heading)
TITLE_CASE_HEADING = re.compile(
    r"^(?:[A-Z][a-z]+\s+){1,8}(?:[A-Z][a-z]*)?$"
)

# Common legal clause title keywords
LEGAL_CLAUSE_KEYWORDS = {
    "confidentiality", "indemnification", "indemnity", "liability",
    "termination", "term", "payment", "intellectual property",
    "governing law", "jurisdiction", "dispute resolution", "arbitration",
    "force majeure", "assignment", "warranties", "warranty",
    "representations", "non-compete", "non-solicitation",
    "data protection", "privacy", "insurance", "audit",
    "compliance", "amendment", "entire agreement", "severability",
    "waiver", "notices", "counterparts", "definitions",
    "recitals", "whereas", "scope", "services", "deliverables",
    "compensation", "fees", "expenses", "renewal", "auto-renewal",
    "limitation of liability", "disclaimer", "background",
    "ownership", "license", "sublicense", "work for hire",
}


@dataclass
class RawSegment:
    """A raw text segment before full metadata assignment."""
    text: str
    title: Optional[str]
    page_number: int
    position: int
    is_heading_followed_by_body: bool = False
    section_number: Optional[str] = None


@dataclass
class ClauseSegment:
    """A fully segmented clause with all required metadata."""
    clause_id: str              # CLAUSE-001, CLAUSE-002, ...
    clause_title: Optional[str]
    clause_text: str
    section: Optional[str]      # Section label e.g., "Section 8" or "1.4"
    page_number: int
    position: int               # Order in document
    word_count: int
    char_count: int
    clause_type: Optional[str]  # Detected legal type


def segment_clauses(
    pages_text: List[Tuple[int, str]],   # [(page_number, text), ...]
    min_length: int = 50,
    max_length: int = 3000,
    document_id: str = "",
) -> List[ClauseSegment]:
    """
    Segment document pages into meaningful legal clauses.

    Args:
        pages_text: List of (page_number, text) tuples
        min_length: Minimum clause text length in chars
        max_length: Maximum clause text length (longer → split further)
        document_id: Used for logging only

    Returns:
        List of ClauseSegment objects with full metadata
    """
    # Step 1: Build a combined text with page markers
    combined_lines: List[Tuple[int, str]] = []  # (page_num, line)
    for page_num, text in pages_text:
        for line in text.split("\n"):
            combined_lines.append((page_num, line))

    # Step 2: Identify split points (clause boundaries)
    raw_segments: List[RawSegment] = []
    current_lines: List[str] = []
    current_page: int = pages_text[0][0] if pages_text else 1
    current_title: Optional[str] = None
    current_section: Optional[str] = None
    position = 0

    def flush_segment():
        nonlocal current_lines, current_title, current_section
        text = "\n".join(current_lines).strip()
        if text and len(text) >= min_length:
            raw_segments.append(RawSegment(
                text=text,
                title=current_title,
                page_number=current_page,
                position=position,
                section_number=current_section,
            ))
        current_lines = []

    for page_num, line in combined_lines:
        stripped = line.strip()
        if not stripped:
            current_lines.append("")
            continue

        is_boundary = _is_clause_boundary(stripped)

        if is_boundary and current_lines:
            flush_segment()
            current_page = page_num
            position += 1
            current_title = _extract_title(stripped)
            current_section = _extract_section_number(stripped)

        current_lines.append(line)

    # Flush last segment
    flush_segment()

    # Step 3: Post-process — merge short segments, split long ones
    processed_segments = _post_process_segments(raw_segments, min_length, max_length)

    # Step 4: Build ClauseSegment objects with full metadata
    clauses: List[ClauseSegment] = []
    for i, seg in enumerate(processed_segments):
        clause_id = f"CLAUSE-{i + 1:03d}"
        clause_type = _detect_clause_type(seg.text, seg.title)

        clauses.append(ClauseSegment(
            clause_id=clause_id,
            clause_title=seg.title,
            clause_text=seg.text.strip(),
            section=seg.section_number or seg.title,
            page_number=seg.page_number,
            position=i,
            word_count=len(seg.text.split()),
            char_count=len(seg.text),
            clause_type=clause_type,
        ))

    logger.info(f"Segmented {len(clauses)} clauses from {len(pages_text)} pages")
    return clauses


def _is_clause_boundary(line: str) -> bool:
    """Determine if a line represents the start of a new clause/section."""
    stripped = line.strip()
    if not stripped:
        return False

    # Check numbered section patterns
    if NUMBERED_SECTION.match(stripped):
        return True

    # Check ALL CAPS heading
    if ALL_CAPS_HEADING.match(stripped) and len(stripped) > 4:
        return True

    # Check for legal keyword headings (case-insensitive)
    lower = stripped.lower()
    for keyword in LEGAL_CLAUSE_KEYWORDS:
        if lower == keyword or lower.startswith(keyword + " ") or lower.endswith(keyword):
            if len(stripped) < 80:  # Headings are short
                return True

    # Check "ARTICLE X — TITLE" pattern
    if re.match(r"^(?:ARTICLE|SECTION|CLAUSE|PART)\s+\w+", stripped, re.IGNORECASE):
        return True

    return False


def _extract_title(line: str) -> Optional[str]:
    """Extract a clean title from a heading line."""
    stripped = line.strip()
    # Remove leading numbers: "1.2.3 Title" → "Title"
    title = re.sub(r"^[\d\.\(\)\s]+", "", stripped)
    # Remove trailing colon
    title = title.rstrip(":")
    # Remove ALL CAPS if it's an all-caps heading
    if title.isupper():
        title = title.title()
    return title.strip() if title.strip() else stripped


def _extract_section_number(line: str) -> Optional[str]:
    """Extract section/article number from heading line."""
    match = re.match(
        r"^((?:\d{1,2}(?:\.\d{1,2}){0,3})|(?:[A-Z]{1,3}\.)|(?:Article\s+\d+)|(?:Section\s+\d+(?:\.\d+)?))",
        line.strip(),
        re.IGNORECASE,
    )
    return match.group(1).strip() if match else None


def _detect_clause_type(text: str, title: Optional[str]) -> Optional[str]:
    """Classify the clause into a legal category based on keywords."""
    combined = (f"{title or ''} {text}").lower()

    clause_type_map = {
        "confidentiality": ["confidential", "non-disclosure", "nda", "proprietary information"],
        "liability": ["liability", "liable", "limitation of liability", "cap on liability"],
        "indemnification": ["indemnif", "indemnity", "hold harmless"],
        "termination": ["terminat", "expir", "end of term", "cancellation"],
        "payment": ["payment", "fees", "compensation", "invoice", "pricing", "remuneration"],
        "intellectual_property": ["intellectual property", "ip rights", "copyright", "patent", "trademark", "work for hire", "ownership"],
        "governing_law": ["governing law", "applicable law", "choice of law"],
        "jurisdiction": ["jurisdiction", "courts of", "venue"],
        "dispute_resolution": ["dispute", "arbitration", "mediation", "adr"],
        "non_compete": ["non-compete", "noncompete", "not compete"],
        "non_solicitation": ["non-solicitation", "nonsolicitation", "not solicit"],
        "force_majeure": ["force majeure", "act of god", "circumstances beyond"],
        "data_privacy": ["data protection", "privacy", "gdpr", "personal data", "data security"],
        "warranty": ["warrant", "warranty", "represent", "guarantee"],
        "insurance": ["insurance", "insured", "coverage", "policy"],
        "assignment": ["assignment", "assign", "transfer of rights"],
        "auto_renewal": ["auto-renew", "automatic renewal", "renew automatically"],
        "audit": ["audit", "inspection right", "records"],
        "compliance": ["compliance", "regulatory", "law and regulation"],
        "definitions": ["definition", "defined term", "means", "shall mean"],
    }

    for clause_type, keywords in clause_type_map.items():
        if any(kw in combined for kw in keywords):
            return clause_type

    return None


def _post_process_segments(
    segments: List[RawSegment],
    min_length: int,
    max_length: int,
) -> List[RawSegment]:
    """
    Merge very short segments into previous segment.
    Split very long segments on paragraph boundaries.
    """
    if not segments:
        return segments

    # Step 1: Merge short segments
    merged: List[RawSegment] = []
    for seg in segments:
        if len(seg.text) < min_length and merged:
            # Append to previous
            prev = merged[-1]
            prev.text = prev.text + "\n\n" + seg.text
        else:
            merged.append(seg)

    # Step 2: Split overly long segments
    result: List[RawSegment] = []
    for seg in merged:
        if len(seg.text) > max_length:
            sub_segs = _split_long_segment(seg, max_length)
            result.extend(sub_segs)
        else:
            result.append(seg)

    return result


def _split_long_segment(seg: RawSegment, max_length: int) -> List[RawSegment]:
    """Split a long segment on paragraph boundaries."""
    paragraphs = re.split(r"\n\n+", seg.text)
    result: List[RawSegment] = []
    current_text = ""
    first = True

    for para in paragraphs:
        if len(current_text) + len(para) > max_length and current_text:
            result.append(RawSegment(
                text=current_text.strip(),
                title=seg.title if first else None,
                page_number=seg.page_number,
                position=seg.position,
                section_number=seg.section_number if first else None,
            ))
            current_text = para
            first = False
        else:
            current_text = current_text + "\n\n" + para if current_text else para

    if current_text.strip():
        result.append(RawSegment(
            text=current_text.strip(),
            title=seg.title if not result else None,
            page_number=seg.page_number,
            position=seg.position,
            section_number=seg.section_number if not result else None,
        ))

    return result if result else [seg]


def segment_from_docx_paragraphs(
    paragraphs: list,  # List[DocxParagraph]
    min_length: int = 50,
    max_length: int = 3000,
) -> List[ClauseSegment]:
    """
    Segment DOCX documents using their heading structure.
    More accurate than text-based segmentation for Word docs.
    """
    from app.ingestion.docx_processor import DocxParagraph

    clauses: List[ClauseSegment] = []
    current_title: Optional[str] = None
    current_text_lines: List[str] = []
    current_page: int = 1
    position = 0

    def flush():
        nonlocal current_title, current_text_lines, position
        text = "\n".join(current_text_lines).strip()
        if text and len(text) >= min_length:
            clause_id = f"CLAUSE-{len(clauses) + 1:03d}"
            clause_type = _detect_clause_type(text, current_title)
            clauses.append(ClauseSegment(
                clause_id=clause_id,
                clause_title=current_title,
                clause_text=text,
                section=current_title,
                page_number=current_page,
                position=position,
                word_count=len(text.split()),
                char_count=len(text),
                clause_type=clause_type,
            ))
            position += 1
        current_title = None
        current_text_lines = []

    for para in paragraphs:
        if para.is_heading and para.level <= 2:
            if current_text_lines:
                flush()
            current_title = para.text
            current_page = para.page_estimate
        else:
            current_text_lines.append(para.text)

    flush()  # Final segment

    return clauses
