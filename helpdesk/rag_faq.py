"""
FAQ RAG (Retrieval Augmented Generation) for Helpdesk.

Stores FAQ chunks in a local ChromaDB persisted directory and retrieves the most
relevant chunks for a given user question.
"""

from __future__ import annotations

import hashlib
import os
from dataclasses import dataclass
from typing import Iterable

import requests


@dataclass(frozen=True)
class RetrievedChunk:
    faq_id: int
    question: str
    answer_chunk: str
    score: float


def _ollama_embeddings(texts: list[str], base_url: str, model: str, timeout: int) -> list[list[float]]:
    """
    Call Ollama embeddings endpoint. Returns a list of embedding vectors.
    """
    out: list[list[float]] = []
    for t in texts:
        r = requests.post(
            f"{base_url.rstrip('/')}/api/embeddings",
            json={"model": model, "prompt": t},
            timeout=timeout,
        )
        r.raise_for_status()
        data = r.json()
        out.append(data["embedding"])
    return out


def _chunk_text(text: str, max_chars: int = 900) -> list[str]:
    text = (text or "").strip()
    if not text:
        return []
    if len(text) <= max_chars:
        return [text]
    chunks: list[str] = []
    start = 0
    while start < len(text):
        end = min(len(text), start + max_chars)
        chunks.append(text[start:end].strip())
        start = end
    return [c for c in chunks if c]


def _stable_id(*parts: str) -> str:
    h = hashlib.sha1()
    for p in parts:
        h.update((p or "").encode("utf-8", errors="ignore"))
        h.update(b"\0")
    return h.hexdigest()


def _get_settings():
    from django.conf import settings

    persist_dir = getattr(settings, "HELPDESK_RAG_PERSIST_DIR", None) or os.path.join(
        settings.BASE_DIR, ".chroma_helpdesk"
    )
    collection = getattr(settings, "HELPDESK_RAG_COLLECTION", "helpdesk_faq")
    ollama_base = getattr(settings, "OLLAMA_BASE_URL", "http://localhost:11434")
    embed_model = getattr(settings, "OLLAMA_EMBED_MODEL", "nomic-embed-text")
    timeout = int(getattr(settings, "OLLAMA_TIMEOUT", 180))
    return persist_dir, collection, ollama_base, embed_model, timeout


def build_or_update_faq_index(faqs: Iterable, rebuild: bool = False) -> int:
    """
    Build (or update) the persisted FAQ index.
    (Disabled for Vercel deployment to reduce bundle size)
    """
    import logging
    logging.getLogger(__name__).warning("ChromaDB FAQ indexing disabled for Vercel deployment.")
    return 0


def retrieve_faq_chunks(query: str, k: int = 4) -> list[RetrievedChunk]:
    """
    Retrieve top-k FAQ chunks relevant to the query.
    (Disabled for Vercel deployment to reduce bundle size)
    """
    import logging
    logging.getLogger(__name__).warning("ChromaDB FAQ retrieval disabled for Vercel deployment.")
    return []

