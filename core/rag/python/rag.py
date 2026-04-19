"""Naive RAG v0: OpenAI embeddings + cosine similarity.

This is the baseline. It exists so every recipe has *something* to import
while core/rag v1 (hybrid + rerank) is in flight. The public API is
deliberately small so the v0 → v1 upgrade won't break recipe code.

Embedding choice: text-embedding-3-small ($0.02 / 1M tokens, 1536 dims).
Cheapest OpenAI option that still gives solid quality for short docs.
Swap via the `embedder` argument if you want a different backend.
"""

from __future__ import annotations

import math
import os
from dataclasses import dataclass, field
from typing import Callable, Iterable

# Embedder signature: batch of strings -> list of float vectors.
Embedder = Callable[[list[str]], list[list[float]]]


def _openai_embedder(batch: list[str]) -> list[list[float]]:
    """Default embedder: OpenAI-compatible endpoint.

    Honors both `OPENAI_BASE_URL` (so it works against Ollama / vLLM /
    any OpenAI-compatible server) and `EMBED_MODEL` (so you can pick
    the right model for your backend — e.g., `nomic-embed-text` on
    Ollama, `text-embedding-3-small` on OpenAI).

    Imported lazily so importing `core.rag` doesn't require `openai`.
    """
    from openai import OpenAI

    client = OpenAI(
        api_key=os.environ.get("OPENAI_API_KEY", "ollama"),
        base_url=os.environ.get("OPENAI_BASE_URL"),
    )
    model = os.getenv("EMBED_MODEL", "text-embedding-3-small")
    resp = client.embeddings.create(model=model, input=batch)
    return [item.embedding for item in resp.data]


def _cosine(a: list[float], b: list[float]) -> float:
    dot = sum(x * y for x, y in zip(a, b))
    na = math.sqrt(sum(x * x for x in a))
    nb = math.sqrt(sum(y * y for y in b))
    return dot / (na * nb) if na and nb else 0.0


@dataclass
class Retriever:
    """A lightweight in-memory retriever. Not a vector DB — v0 keeps it simple."""

    docs: list[str] = field(default_factory=list)
    vectors: list[list[float]] = field(default_factory=list)
    embedder: Embedder = field(default=_openai_embedder)

    def add(self, new_docs: Iterable[str]) -> None:
        """Embed and add new documents to the index."""
        new_docs = list(new_docs)
        if not new_docs:
            return
        self.vectors.extend(self.embedder(new_docs))
        self.docs.extend(new_docs)

    def retrieve(self, query: str, k: int = 5) -> list[tuple[str, float]]:
        """Return top-k (doc, score) tuples, most relevant first."""
        if not self.docs:
            return []
        (q_vec,) = self.embedder([query])
        scored = [(self.docs[i], _cosine(q_vec, self.vectors[i])) for i in range(len(self.docs))]
        scored.sort(key=lambda t: t[1], reverse=True)
        return scored[:k]


def index(docs: Iterable[str], embedder: Embedder = _openai_embedder) -> Retriever:
    """Functional API: build a Retriever from a list of docs."""
    r = Retriever(embedder=embedder)
    r.add(docs)
    return r


def retrieve(query: str, k: int, retriever: Retriever) -> list[tuple[str, float]]:
    """Functional API: retrieve top-k from an existing Retriever."""
    return retriever.retrieve(query, k)
