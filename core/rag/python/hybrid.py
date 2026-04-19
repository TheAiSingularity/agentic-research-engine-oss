"""Hybrid retrieval: BM25 (sparse) + dense embeddings + Reciprocal Rank Fusion.

Two-stage RAG pipeline in 2026 is hybrid retrieval → cross-encoder rerank.
This module owns the hybrid-retrieval stage. Reranking lives in rerank.py.

Primary sources:
  - RAG review 2025-2026 (RAGFlow blog)
  - Benchmarking retrieval for financial docs (arXiv 2604.01733):
    two-stage = Recall@5 0.816, MRR@3 0.605, outperforms all single-stage.

Design notes:
  - Sparse (BM25) catches exact tokens / rare strings / numbers that dense embeddings miss.
  - Dense catches paraphrases / semantic matches that BM25 misses.
  - RRF (k=60) fuses the two rank lists without needing to normalize scores
    across methods, which is why it's the SOTA fusion choice in 2026.
"""

from __future__ import annotations

import re
from dataclasses import dataclass, field
from typing import Callable, Iterable

from rank_bm25 import BM25Okapi

from .rag import Embedder, _cosine, _openai_embedder

RRF_K = 60  # standard choice in the RAG literature


_tok_re = re.compile(r"\w+")


def _tokenize(text: str) -> list[str]:
    """Lowercase word-token stream — fine for BM25 over English + code/URLs."""
    return _tok_re.findall(text.lower())


def _rrf_fuse(rank_lists: list[list[int]], k: int = RRF_K) -> list[tuple[int, float]]:
    """Reciprocal Rank Fusion over N rank lists of document ids.

    Each entry in a rank list is a doc id; position in the list is the rank.
    Returns (doc_id, fused_score) sorted by score descending.
    """
    scores: dict[int, float] = {}
    for ranks in rank_lists:
        for rank, doc_id in enumerate(ranks):
            scores[doc_id] = scores.get(doc_id, 0.0) + 1.0 / (k + rank + 1)
    return sorted(scores.items(), key=lambda t: t[1], reverse=True)


@dataclass
class HybridRetriever:
    """BM25 + dense + RRF.

    Usage:
        h = HybridRetriever()
        h.add(["doc 1", "doc 2", ...])
        top = h.retrieve("query", k=50)  # returns [(doc, score), ...]
    """

    docs: list[str] = field(default_factory=list)
    vectors: list[list[float]] = field(default_factory=list)
    embedder: Embedder = field(default=_openai_embedder)
    _bm25: BM25Okapi | None = field(default=None, repr=False)
    _tokenized: list[list[str]] = field(default_factory=list, repr=False)

    def add(self, new_docs: Iterable[str]) -> None:
        """Embed, tokenize, and index new documents."""
        new_docs = list(new_docs)
        if not new_docs:
            return
        self.vectors.extend(self.embedder(new_docs))
        self._tokenized.extend(_tokenize(d) for d in new_docs)
        self.docs.extend(new_docs)
        # Rebuild BM25 (the library doesn't support incremental add).
        self._bm25 = BM25Okapi(self._tokenized)

    def _bm25_ranks(self, query: str) -> list[int]:
        scores = self._bm25.get_scores(_tokenize(query)) if self._bm25 else []
        return sorted(range(len(self.docs)), key=lambda i: scores[i], reverse=True)

    def _dense_ranks(self, query: str) -> list[int]:
        if not self.docs:
            return []
        (q_vec,) = self.embedder([query])
        scores = [_cosine(q_vec, self.vectors[i]) for i in range(len(self.docs))]
        return sorted(range(len(self.docs)), key=lambda i: scores[i], reverse=True)

    def retrieve(self, query: str, k: int = 50) -> list[tuple[str, float]]:
        """Hybrid retrieve top-k. Returns [(doc_text, rrf_score), …]."""
        if not self.docs:
            return []
        fused = _rrf_fuse([self._bm25_ranks(query), self._dense_ranks(query)])
        return [(self.docs[doc_id], score) for doc_id, score in fused[:k]]


def hybrid_index(
    docs: Iterable[str],
    embedder: Embedder = _openai_embedder,
) -> HybridRetriever:
    """Functional API mirror of `core.rag.index`."""
    r = HybridRetriever(embedder=embedder)
    r.add(docs)
    return r
