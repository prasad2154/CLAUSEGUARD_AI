"""
LLM Client — Configurable LLM interface.
Supports OpenAI, Azure OpenAI, and Ollama via env configuration.
"""

import json
import logging
import time
from typing import Optional, Dict, Any

from app.config import get_settings

logger = logging.getLogger(__name__)
settings = get_settings()

_llm_client = None


def get_llm():
    """Get configured LangChain LLM instance."""
    global _llm_client
    if _llm_client is None:
        _llm_client = _build_llm()
    return _llm_client


def _build_llm():
    """Build LLM based on configuration."""
    try:
        from langchain_openai import ChatOpenAI

        kwargs = {
            "model": settings.llm_model,
            "temperature": settings.llm_temperature,
            "max_tokens": settings.llm_max_tokens,
            "timeout": 120,
        }

        if settings.openai_api_key:
            kwargs["api_key"] = settings.openai_api_key

        if settings.openai_base_url and settings.openai_base_url != "https://api.openai.com/v1":
            kwargs["base_url"] = settings.openai_base_url

        logger.info(f"LLM configured: {settings.llm_model} via {settings.llm_provider}")
        return ChatOpenAI(**kwargs)

    except Exception as e:
        logger.error(f"Failed to build LLM client: {e}")
        raise RuntimeError(f"LLM initialization failed: {e}")


def call_llm_json(prompt: str, max_retries: int = 2) -> Optional[Dict[str, Any]]:
    """
    Call LLM and parse JSON response.
    Returns parsed dict or None on failure.
    """
    llm = get_llm()

    for attempt in range(max_retries + 1):
        try:
            response = llm.invoke(prompt)
            content = response.content if hasattr(response, "content") else str(response)

            # Extract JSON from response (handle markdown code blocks)
            json_str = _extract_json(content)
            if json_str:
                return json.loads(json_str)
            else:
                logger.warning(f"LLM response did not contain valid JSON (attempt {attempt + 1})")

        except json.JSONDecodeError as e:
            logger.warning(f"JSON parse error (attempt {attempt + 1}): {e}")
        except Exception as e:
            logger.error(f"LLM call failed (attempt {attempt + 1}): {e}")
            if attempt == max_retries:
                raise

        if attempt < max_retries:
            time.sleep(1)

    return None


def _extract_json(text: str) -> Optional[str]:
    """Extract JSON from LLM response, handling markdown code blocks."""
    import re

    # Try to find JSON in code blocks
    code_block = re.search(r"```(?:json)?\s*([\s\S]+?)\s*```", text)
    if code_block:
        return code_block.group(1)

    # Try to find raw JSON object
    json_match = re.search(r"\{[\s\S]+\}", text)
    if json_match:
        return json_match.group(0)

    return text.strip() if text.strip().startswith("{") else None


def check_llm_available() -> Dict[str, Any]:
    """Check if LLM is configured and reachable."""
    start = time.time()
    try:
        if not settings.openai_api_key and settings.openai_base_url == "https://api.openai.com/v1":
            return {
                "available": False,
                "error": "OPENAI_API_KEY not configured",
                "model": settings.llm_model,
            }

        llm = get_llm()
        # Light ping
        response = llm.invoke("Respond with: OK")
        latency = (time.time() - start) * 1000
        return {
            "available": True,
            "model": settings.llm_model,
            "latency_ms": latency,
        }
    except Exception as e:
        return {
            "available": False,
            "error": str(e),
            "model": settings.llm_model,
            "latency_ms": (time.time() - start) * 1000,
        }
