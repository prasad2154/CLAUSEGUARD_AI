"""
ClauseGuard AI — RAGAS Evaluation Pipeline
Evaluates Q&A quality using Faithfulness, Answer Relevancy, and Context Recall metrics.

Usage:
  python evaluation/ragas_eval.py --document_id <id> --base_url http://localhost:8000

Requirements:
  pip install ragas datasets
"""

import argparse
import json
import logging
import sys
import time
from typing import List, Dict, Any

import httpx

logger = logging.getLogger(__name__)
logging.basicConfig(level=logging.INFO, format="%(levelname)s - %(message)s")

# ─── Standard Evaluation Questions ──────────────────────────────────────────

EVAL_QUESTIONS = [
    "What is the governing law clause in this contract?",
    "What are the liability limitations mentioned?",
    "What are the payment terms?",
    "What are the termination conditions?",
    "Is there a confidentiality or NDA clause?",
    "What is the contract term or duration?",
    "Are there any indemnification clauses?",
    "What jurisdiction governs disputes?",
    "Are there any non-compete or non-solicitation clauses?",
    "What happens upon breach of contract?",
]


def query_clauseguard(base_url: str, document_id: str, question: str) -> Dict[str, Any]:
    """Send a question to ClauseGuard Q&A API and return the response."""
    try:
        resp = httpx.post(
            f"{base_url}/api/query",
            json={"document_id": document_id, "question": question},
            timeout=30.0
        )
        resp.raise_for_status()
        return resp.json()
    except Exception as e:
        logger.error(f"Query failed: {e}")
        return {"answer": "", "citations": [], "confidence": 0.0, "has_evidence": False}


def build_ragas_dataset(base_url: str, document_id: str) -> List[Dict]:
    """Build RAGAS evaluation dataset from ClauseGuard Q&A responses."""
    logger.info(f"Building RAGAS dataset for document {document_id}")
    samples = []

    for q in EVAL_QUESTIONS:
        logger.info(f"  Querying: {q}")
        result = query_clauseguard(base_url, document_id, q)

        # Extract contexts from citations
        contexts = [c["text"] for c in result.get("citations", []) if c.get("text")]

        sample = {
            "question": q,
            "answer": result.get("answer", ""),
            "contexts": contexts,
            "ground_truth": "",  # Would need human annotation for full eval
            "confidence": result.get("confidence", 0.0),
            "has_evidence": result.get("has_evidence", False),
            "citation_count": len(contexts),
        }
        samples.append(sample)
        time.sleep(0.5)  # Avoid overwhelming the backend

    return samples


def compute_simple_metrics(samples: List[Dict]) -> Dict[str, float]:
    """
    Compute lightweight proxy metrics without LLM-graded RAGAS evaluation.
    (Full RAGAS eval requires an LLM judge which adds cost.)
    """
    total = len(samples)
    if total == 0:
        return {}

    answered = sum(1 for s in samples if len(s["answer"]) > 50)
    grounded = sum(1 for s in samples if s["has_evidence"] and s["citation_count"] > 0)
    avg_confidence = sum(s["confidence"] for s in samples) / total
    avg_citations = sum(s["citation_count"] for s in samples) / total

    return {
        "total_questions": total,
        "answered_pct": round(answered / total * 100, 1),
        "grounded_pct": round(grounded / total * 100, 1),
        "avg_confidence": round(avg_confidence, 3),
        "avg_citations_per_answer": round(avg_citations, 2),
        "hallucination_risk": round((1 - grounded / total) * 100, 1),
    }


def run_full_ragas_eval(samples: List[Dict]) -> None:
    """
    Run RAGAS faithfulness and answer relevancy evaluation.
    Requires: OPENAI_API_KEY or compatible LLM configured.
    """
    try:
        from ragas import evaluate
        from ragas.metrics import faithfulness, answer_relevancy, context_recall
        from datasets import Dataset

        dataset = Dataset.from_list([
            {
                "question": s["question"],
                "answer": s["answer"],
                "contexts": s["contexts"] if s["contexts"] else ["No context retrieved"],
                "ground_truth": s["ground_truth"] or s["answer"],
            }
            for s in samples
        ])

        logger.info("Running RAGAS evaluation (faithfulness, answer_relevancy)...")
        results = evaluate(
            dataset=dataset,
            metrics=[faithfulness, answer_relevancy],
        )
        logger.info("\n=== RAGAS Scores ===")
        for metric, score in results.items():
            logger.info(f"  {metric}: {score:.4f}")

        return results

    except ImportError:
        logger.warning("RAGAS not installed or not configured. Skipping LLM evaluation.")
        return None
    except Exception as e:
        logger.error(f"RAGAS evaluation failed: {e}")
        return None


def main():
    parser = argparse.ArgumentParser(description="ClauseGuard AI — RAGAS Evaluation")
    parser.add_argument("--document_id", required=True, help="Document ID to evaluate Q&A on")
    parser.add_argument("--base_url", default="http://localhost:8000", help="Backend base URL")
    parser.add_argument("--output", default="evaluation/results.json", help="Output file path")
    parser.add_argument("--full_ragas", action="store_true", help="Run LLM-graded RAGAS metrics")
    args = parser.parse_args()

    logger.info(f"ClauseGuard AI RAGAS Evaluation")
    logger.info(f"  Document:   {args.document_id}")
    logger.info(f"  Backend:    {args.base_url}")

    # Step 1: Build Q&A samples
    samples = build_ragas_dataset(args.base_url, args.document_id)

    if not samples:
        logger.error("No samples generated. Check backend connectivity.")
        sys.exit(1)

    # Step 2: Compute lightweight proxy metrics
    proxy_metrics = compute_simple_metrics(samples)

    logger.info("\n=== Proxy Metrics (No LLM Judge) ===")
    for k, v in proxy_metrics.items():
        logger.info(f"  {k}: {v}")

    # Step 3: Optional full RAGAS evaluation
    ragas_results = None
    if args.full_ragas:
        ragas_results = run_full_ragas_eval(samples)

    # Step 4: Save results
    output = {
        "document_id": args.document_id,
        "proxy_metrics": proxy_metrics,
        "ragas_scores": ragas_results,
        "samples": samples,
    }

    import os
    os.makedirs(os.path.dirname(args.output), exist_ok=True)
    with open(args.output, "w") as f:
        json.dump(output, f, indent=2)

    logger.info(f"\nResults saved to: {args.output}")

    # Report grounding quality
    grounded_pct = proxy_metrics.get("grounded_pct", 0)
    if grounded_pct >= 80:
        logger.info("✅ PASS: >= 80% of answers are citation-grounded")
    else:
        logger.warning(f"⚠️  WARN: Only {grounded_pct}% of answers are citation-grounded")


if __name__ == "__main__":
    main()
