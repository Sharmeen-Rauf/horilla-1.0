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

    Returns number of chunks upserted.
    """
    import chromadb

    persist_dir, collection_name, ollama_base, embed_model, timeout = _get_settings()
    client = chromadb.PersistentClient(path=persist_dir)

    if rebuild:
        try:
            client.delete_collection(collection_name)
        except Exception:
            pass

    col = client.get_or_create_collection(name=collection_name)

    ids: list[str] = []
    docs: list[str] = []
    metas: list[dict] = []

    for faq in faqs:
        chunks = _chunk_text(faq.answer)
        for idx, ch in enumerate(chunks):
            doc = f"Q: {faq.question}\nA: {ch}"
            ids.append(_stable_id(str(faq.id), str(idx), faq.question, ch))
            docs.append(doc)
            metas.append(
                {
                    "faq_id": int(faq.id),
                    "question": faq.question,
                    "chunk_index": idx,
                }
            )

    if not ids:
        return 0

    embeddings = _ollama_embeddings(docs, ollama_base, embed_model, timeout)
    col.upsert(ids=ids, documents=docs, metadatas=metas, embeddings=embeddings)
    return len(ids)


def retrieve_faq_chunks(query: str, k: int = 4) -> list[RetrievedChunk]:
    """
    Retrieve top-k FAQ chunks relevant to the query.
    """
    import chromadb

    persist_dir, collection_name, ollama_base, embed_model, timeout = _get_settings()
    client = chromadb.PersistentClient(path=persist_dir)
    col = client.get_or_create_collection(name=collection_name)

    emb = _ollama_embeddings([query], ollama_base, embed_model, timeout)[0]
    res = col.query(query_embeddings=[emb], n_results=k, include=["documents", "metadatas", "distances"])

    docs = (res.get("documents") or [[]])[0]
    metas = (res.get("metadatas") or [[]])[0]
    dists = (res.get("distances") or [[]])[0]

    out: list[RetrievedChunk] = []
    for doc, meta, dist in zip(docs, metas, dists):
        faq_id = int(meta.get("faq_id", 0) or 0)
        question = meta.get("question", "") or ""
        # Chroma returns distances (lower = closer). Convert to a rough score.
        score = float(1 / (1 + float(dist))) if dist is not None else 0.0
        # extract answer chunk if doc formatted as Q/A
        answer_chunk = doc.split("\nA:", 1)[-1].strip() if isinstance(doc, str) else ""
        out.append(RetrievedChunk(faq_id=faq_id, question=question, answer_chunk=answer_chunk, score=score))
    return out

