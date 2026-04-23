"""
AI service for Helpdesk using Ollama (local LLM).
Calls Ollama HTTP API at http://localhost:11434
"""

import logging
from urllib.parse import urljoin

import requests

logger = logging.getLogger(__name__)

OLLAMA_BASE_URL = "http://localhost:11434"


def _get_model():
    try:
        from django.conf import settings
        return getattr(settings, "OLLAMA_MODEL", "llama3.2")
    except Exception:
        return "llama3.2"


def _get_timeout():
    try:
        from django.conf import settings
        return getattr(settings, "OLLAMA_TIMEOUT", 180)
    except Exception:
        return 180


def get_available_models():
    """List models available in Ollama."""
    try:
        r = requests.get(
            urljoin(OLLAMA_BASE_URL, "/api/tags"),
            timeout=10,
        )
        r.raise_for_status()
        data = r.json()
        return [m.get("name", "") for m in data.get("models", [])]
    except Exception as e:
        logger.warning("Could not fetch Ollama models: %s", e)
        return []


def chat(messages: list[dict], model: str = None) -> str:
    """
    Send chat messages to Ollama and return the assistant reply.

    Args:
        messages: List of {"role": "user"|"assistant"|"system", "content": "..."}
        model: Ollama model name (e.g. llama3.2, mistral)

    Returns:
        Assistant reply text, or error message if call fails.
    """
    if model is None:
        model = _get_model()
    timeout = _get_timeout()
    try:
        r = requests.post(
            urljoin(OLLAMA_BASE_URL, "/api/chat"),
            json={"model": model, "messages": messages, "stream": False},
            timeout=timeout,
        )
        r.raise_for_status()
        data = r.json()
        return data.get("message", {}).get("content", "").strip()
    except requests.exceptions.ConnectionError:
        return (
            "Ollama is not running. Please start Ollama and ensure a model is pulled "
            "(e.g. ollama pull llama3.2)."
        )
    except requests.exceptions.Timeout:
        return "The request timed out. Try a shorter question or a smaller model."
    except Exception as e:
        logger.exception("Ollama chat error: %s", e)
        return f"An error occurred: {str(e)}"
