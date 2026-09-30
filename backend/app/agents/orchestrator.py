"""
LangGraph Orchestrator — Manages the multi-agent contract review workflow.
"""

import logging
from typing import List, Dict, Any, TypedDict, Annotated
import operator

from app.schemas import RiskItem, MissingClauseItem
from app.agents.risk_agent import run_risk_detection
from app.agents.missing_clause_agent import run_missing_clause_detection
from app.agents.compliance_agent import run_compliance_check
from app.agents.synthesis_agent import run_synthesis
from app.agents.prompts import CONTRACT_CLASSIFICATION_PROMPT
from app.agents.llm_client import call_llm_json

try:
    from langgraph.graph import StateGraph, END
except ImportError:
    # Handle if langgraph not installed or different version
    StateGraph = None

logger = logging.getLogger(__name__)

class ReviewState(TypedDict):
    """The state passed between agents in the workflow."""
    document_id: str
    document_name: str
    contract_type: str
    clauses: List[Dict[str, Any]]
    indexed_clause_ids: set
    
    # Outputs appended by agents
    risks: Annotated[List[RiskItem], operator.add]
    missing_clauses: Annotated[List[MissingClauseItem], operator.add]
    
    # Final outputs
    summary: str
    recommendations: List[str]
    agent_log: Annotated[List[str], operator.add]


def node_classify_contract(state: ReviewState) -> Dict[str, Any]:
    """Classify the contract if type is unknown."""
    if state["contract_type"] and state["contract_type"] != "General Contract":
        return {"agent_log": ["Classification skipped (already known)."]}

    logger.info("Classifying contract type")
    
    # Get first few clauses text
    text_sample = "\n".join(
        [c.get("clause_text", "") for c in state["clauses"][:5]]
    )[:2000]

    prompt = CONTRACT_CLASSIFICATION_PROMPT.format(
        text_sample=text_sample,
        filename=state["document_name"]
    )
    
    try:
        result = call_llm_json(prompt)
        if result and "contract_type" in result:
            logger.info(f"Classified as: {result['contract_type']}")
            return {
                "contract_type": result["contract_type"],
                "agent_log": [f"Classified contract as {result['contract_type']}"]
            }
    except Exception as e:
        logger.warning(f"Classification LLM call failed, falling back: {e}")
    
    return {"agent_log": ["Classification fallback to General Contract."]}


def node_detect_risks(state: ReviewState) -> Dict[str, Any]:
    """Run risk detection agent."""
    logger.info("Running risk detection")
    risks = run_risk_detection(
        clauses=state["clauses"],
        contract_type=state["contract_type"],
        indexed_clause_ids=state["indexed_clause_ids"]
    )
    return {
        "risks": risks,
        "agent_log": [f"Risk agent found {len(risks)} risks."]
    }


def node_detect_missing_clauses(state: ReviewState) -> Dict[str, Any]:
    """Run missing clause agent."""
    logger.info("Running missing clause detection")
    missing = run_missing_clause_detection(
        clauses=state["clauses"],
        contract_type=state["contract_type"]
    )
    return {
        "missing_clauses": missing,
        "agent_log": [f"Missing clause agent found {len(missing)} missing clauses."]
    }


def node_compliance_check(state: ReviewState) -> Dict[str, Any]:
    """Run compliance playbook agent."""
    logger.info("Running compliance checks")
    compliance_risks = run_compliance_check(
        clauses=state["clauses"],
        contract_type=state["contract_type"],
        indexed_clause_ids=state["indexed_clause_ids"]
    )
    return {
        "risks": compliance_risks,
        "agent_log": [f"Compliance agent found {len(compliance_risks)} issues."]
    }


def node_synthesis(state: ReviewState) -> Dict[str, Any]:
    """Synthesize findings into an executive summary."""
    logger.info("Running synthesis")
    result = run_synthesis(
        document_name=state["document_name"],
        contract_type=state["contract_type"],
        risks=state["risks"],
        missing_clauses=state["missing_clauses"]
    )
    return {
        "summary": result["summary"],
        "recommendations": result["recommendations"],
        "agent_log": ["Synthesis complete."]
    }


def build_review_graph():
    """Build the LangGraph StateGraph for the review workflow."""
    if StateGraph is None:
        raise ImportError("langgraph is not available.")
        
    workflow = StateGraph(ReviewState)
    
    # Add nodes
    workflow.add_node("classify", node_classify_contract)
    workflow.add_node("risk_detection", node_detect_risks)
    workflow.add_node("missing_clauses", node_detect_missing_clauses)
    workflow.add_node("compliance", node_compliance_check)
    workflow.add_node("synthesis", node_synthesis)
    
    # Define edges (Workflow: Classify -> (Risk, Missing, Compliance) -> Synthesis)
    workflow.set_entry_point("classify")
    
    # Sequential for simplicity and reliability, but conceptually parallel
    workflow.add_edge("classify", "risk_detection")
    workflow.add_edge("risk_detection", "missing_clauses")
    workflow.add_edge("missing_clauses", "compliance")
    workflow.add_edge("compliance", "synthesis")
    workflow.add_edge("synthesis", END)
    
    return workflow.compile()


def run_agentic_review(
    document_id: str,
    document_name: str,
    contract_type: str,
    clauses: List[Dict[str, Any]],
) -> Dict[str, Any]:
    """
    Entry point to run the full LangGraph review workflow.
    """
    logger.info(f"Starting agentic review for document {document_id}")
    
    indexed_clause_ids = {c.get("clause_id") for c in clauses if c.get("clause_id")}
    
    initial_state = {
        "document_id": document_id,
        "document_name": document_name,
        "contract_type": contract_type or "General Contract",
        "clauses": clauses,
        "indexed_clause_ids": indexed_clause_ids,
        "risks": [],
        "missing_clauses": [],
        "summary": "",
        "recommendations": [],
        "agent_log": ["Workflow started."]
    }

    try:
        graph = build_review_graph()
        # In langgraph 0.1+, invoke returns the final state dict
        final_state = graph.invoke(initial_state)
        
        return {
            "document_name": final_state.get("document_name", document_name),
            "contract_type": final_state["contract_type"],
            "risks": final_state["risks"],
            "missing_clauses": final_state["missing_clauses"],
            "summary": final_state["summary"],
            "recommendations": final_state["recommendations"],
            "agent_log": final_state["agent_log"]
        }
        
    except Exception as e:
        logger.error(f"Agentic review workflow failed: {e}")
        # Fallback to sequential execution if langgraph fails
        return _fallback_sequential_review(initial_state)


def _fallback_sequential_review(state: dict) -> Dict[str, Any]:
    """Fallback if LangGraph fails to initialize or run."""
    logger.warning("Running fallback sequential review (without LangGraph)")
    
    try:
        state.update(node_classify_contract(state))
        
        risk_res = node_detect_risks(state)
        state["risks"].extend(risk_res["risks"])
        
        missing_res = node_detect_missing_clauses(state)
        state["missing_clauses"].extend(missing_res["missing_clauses"])
        
        comp_res = node_compliance_check(state)
        state["risks"].extend(comp_res["risks"])
        
        synth_res = node_synthesis(state)
        state.update(synth_res)
        
        return {
            "document_name": state.get("document_name", "Contract Document"),
            "contract_type": state["contract_type"],
            "risks": state["risks"],
            "missing_clauses": state["missing_clauses"],
            "summary": state["summary"],
            "recommendations": state["recommendations"],
            "agent_log": state["agent_log"] + ["Ran via sequential fallback."]
        }
    except Exception as e:
        logger.error(f"Fallback review failed: {e}")
        raise
