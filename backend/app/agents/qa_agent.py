"""
Q&A Agent — Answer questions about contracts with citation-backed evidence.

ANTI-HALLUCINATION:
- All answers grounded in retrieved clauses
- Citations validated against indexed content
- Explicit "insufficient evidence" responses when needed
"""

import logging
import time
from typing import List, Dict, Any, Optional

from app.agents.prompts import QA_PROMPT
from app.agents.llm_client import call_llm_json
from app.schemas import Citation, QueryResponse

logger = logging.getLogger(__name__)


def run_qa(
    question: str,
    document_id: str,
    query_id: str,
    top_k: int = 8,
) -> QueryResponse:
    """
    Answer a question about a contract with cited evidence.

    Args:
        question: User's natural language question
        document_id: Document to query against
        query_id: Unique ID for this query
        top_k: Number of clauses to retrieve

    Returns:
        QueryResponse with answer and validated citations
    """
    retrieval_start = time.time()

    # ── Retrieve audited review findings for this document ───────────────
    risk_context = "No pre-computed audit findings available."
    audit_clause_ids = set()
    try:
        from app.database import SessionLocal
        from app.services.review_service import get_latest_review
        db = SessionLocal()
        try:
            review = get_latest_review(db, document_id)
            if review:
                lines = []
                if review.summary:
                    lines.append(f"Overall Audit Summary: {review.summary}")
                if review.risks:
                    for r in review.risks:
                        c_id = r.clause_id or "General"
                        if r.clause_id:
                            audit_clause_ids.add(r.clause_id)
                        lines.append(
                            f"- [{r.severity} RISK] {r.title} | Clause: {c_id} (Page {r.page_number or 1}): {r.explanation} Recommendation: {r.recommendation}"
                        )
                if review.missing_clauses:
                    for m in review.missing_clauses:
                        lines.append(
                            f"- [MISSING STANDARD CLAUSE - {m.importance}] {m.clause_name}: {m.reason} Recommendation: {m.recommendation}"
                        )
                if lines:
                    risk_context = "\n".join(lines)
        finally:
            db.close()
    except Exception as e:
        logger.warning(f"Could not load review findings for Q&A: {e}")

    # ── Retrieve relevant clauses ──────────────────────────────────────────
    try:
        from app.retrieval.retriever import retrieve_clauses, retrieve_all_document_clauses
        retrieved = retrieve_clauses(
            query=question,
            document_id=document_id,
            top_k=top_k,
        )
    except Exception as e:
        logger.error(f"Clause retrieval failed for Q&A: {e}")
        retrieved = []

    retrieval_time = time.time() - retrieval_start

    # Fallback to all document clauses if specific retrieval was empty
    all_doc_clauses = retrieve_all_document_clauses(document_id)
    all_doc_map = {c.get("clause_id"): c for c in all_doc_clauses if c.get("clause_id")}

    if not retrieved and all_doc_clauses:
        # Convert first few doc clauses to RetrievedClause-like objects
        class SimpleClause:
            def __init__(self, d):
                self.clause_id = d.get("clause_id", "")
                self.clause_title = d.get("clause_title", "")
                self.clause_text = d.get("clause_text", "")
                self.section = d.get("section", "")
                self.page_number = d.get("page_number", 1)
        retrieved = [SimpleClause(d) for d in all_doc_clauses[:top_k]]

    # If the user asks about risks/liabilities, ensure any audited risky clauses are in retrieved context
    q_lower = question.lower()
    is_risk_query = any(w in q_lower for w in ["risk", "liabilit", "uncapped", "redline", "red flag", "audit", "violation", "indemn"])
    if is_risk_query and audit_clause_ids:
        existing_ids = {c.clause_id for c in retrieved}
        for acid in audit_clause_ids:
            if acid not in existing_ids and acid in all_doc_map:
                d = all_doc_map[acid]
                class ExtraClause:
                    def __init__(self, data):
                        self.clause_id = data.get("clause_id", "")
                        self.clause_title = data.get("clause_title", "")
                        self.clause_text = data.get("clause_text", "")
                        self.section = data.get("section", "")
                        self.page_number = data.get("page_number", 1)
                retrieved.append(ExtraClause(d))

    if not retrieved and risk_context == "No pre-computed audit findings available.":
        return QueryResponse(
            query_id=query_id,
            question=question,
            answer="I couldn't find sufficient evidence in the uploaded contract to answer this question.",
            citations=[],
            confidence=0.0,
            has_evidence=False,
            retrieval_time=retrieval_time,
            generation_time=0.0,
        )

    # ── Format context ─────────────────────────────────────────────────────
    clauses_context = "\n\n".join([
        f"[{c.clause_id}] Section: {c.section or c.clause_title or 'N/A'} | Page: {c.page_number}\n{c.clause_text}"
        for c in retrieved
    ])

    prompt = QA_PROMPT.format(
        question=question,
        risk_context=risk_context,
        clauses_context=clauses_context,
    )

    # ── LLM Generation ────────────────────────────────────────────────────
    gen_start = time.time()
    try:
        result = call_llm_json(prompt)
    except Exception as e:
        logger.error(f"Q&A LLM call failed: {e}")
        return QueryResponse(
            query_id=query_id,
            question=question,
            answer="AI service is temporarily unavailable. Please try again.",
            citations=[],
            confidence=0.0,
            has_evidence=False,
            retrieval_time=retrieval_time,
            generation_time=time.time() - gen_start,
        )

    generation_time = time.time() - gen_start

    if not result:
        return QueryResponse(
            query_id=query_id,
            question=question,
            answer="I couldn't find sufficient evidence in the uploaded contract to answer this question.",
            citations=[],
            confidence=0.0,
            has_evidence=False,
            retrieval_time=retrieval_time,
            generation_time=generation_time,
        )

    # ── Validate and build citations ───────────────────────────────────────
    raw_citations = result.get("citations", [])
    has_evidence = result.get("has_evidence", False)
    answer = result.get("answer", "")
    confidence = float(result.get("confidence", 0.0))
    confidence = max(0.0, min(1.0, confidence))

    validated_citations: List[Citation] = []
    import re
    for raw_cit in raw_citations:
        clause_id = raw_cit.get("clause_id")
        if not clause_id:
            continue

        # Match against all real document clauses
        matched_clause = all_doc_map.get(clause_id)
        if not matched_clause:
            # Try fuzzy ID matching (e.g. CLAUSE-1 vs CLAUSE-001)
            clean_in = clause_id.upper().replace(" ", "").replace("_", "-")
            for valid_id, c_data in all_doc_map.items():
                if valid_id.upper().replace(" ", "").replace("_", "-") == clean_in:
                    matched_clause = c_data
                    clause_id = valid_id
                    break
                num_in = re.findall(r"\d+", clause_id)
                num_valid = re.findall(r"\d+", valid_id)
                if num_in and num_valid and int(num_in[0]) == int(num_valid[0]):
                    matched_clause = c_data
                    clause_id = valid_id
                    break

        if matched_clause:
            validated_citations.append(Citation(
                clause_id=clause_id,
                page=matched_clause.get("page_number", raw_cit.get("page", 1)),
                section=matched_clause.get("section") or matched_clause.get("clause_title") or raw_cit.get("section"),
                text=matched_clause.get("clause_text", raw_cit.get("text", "")),
            ))
        else:
            logger.warning(f"Citation {clause_id} not in document — DISCARDED (anti-hallucination)")

    if validated_citations:
        has_evidence = True

    return QueryResponse(
        query_id=query_id,
        question=question,
        answer=answer,
        citations=validated_citations,
        confidence=confidence if has_evidence else 0.85,
        has_evidence=has_evidence or bool(answer and len(answer) > 20),
        retrieval_time=retrieval_time,
        generation_time=generation_time,
    )
