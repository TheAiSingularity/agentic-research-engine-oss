"""Cross-encoder reranking — second stage of the 2026 two-stage RAG pipeline.

Why: hybrid retrieval (BM25 + dense + RRF) maximizes recall at some k.
A cross-encoder then re-scores (query, passage) pairs with full attention
and picks the best few. Published benchmarks: rerank top-50 candidates
in ~1.5s on a modern GPU; massive MRR gains over cosine alone.

Default model: BAAI/bge-reranker-v2-m3 — strong open-source cross-encoder,
reasonable memory footprint, multilingual, Apache 2.0.

sentence-transformers is loaded lazily so importing this module doesn't
force the dependency for users who only want hybrid retrieval.
"""

from __future__ import annotations

import os
from dataclasses import dataclass, field

RERANKER_MODEL = os.getenv("RERANKER_MODEL", "BAAI/bge-reranker-v2-m3")


class _LazyCrossEncoder:
    """Delay sentence-transformers import until first use."""

    def __init__(self, model_name: str):
        self.model_name = model_name
        self._impl = None

    def predict(self, pairs: list[tuple[str, str]]) -> list[float]:
        if self._impl is None:
            try:
                from sentence_transformers import CrossEncoder  # type: ignore
            except ImportError as e:  # pragma: no cover
                raise ImportError(
                    "sentence-transformers is required for reranking. "
                    "Install with: pip install 'sentence-transformers>=3.0.0'"
                ) from e
            self._impl = CrossEncoder(self.model_name)
        return list(self._impl.predict(pairs))


@dataclass
class CrossEncoderReranker:
    """Rerank a list of candidate passages against a query."""

    model_name: str = RERANKER_MODEL
    _ce: _LazyCrossEncoder = field(init=False)

    def __post_init__(self) -> None:
        self._ce = _LazyCrossEncoder(self.model_name)

    def rerank(
        self,
        query: str,
        candidates: list[tuple[str, float]] | list[str],
        k: int = 8,
    ) -> list[tuple[str, float]]:
        """Return top-k (passage, rerank_score), sorted by score desc.

        `candidates` can be the raw output of HybridRetriever.retrieve() —
        prior scores are ignored (the cross-encoder re-scores from scratch).
        """
        passages = [c[0] if isinstance(c, tuple) else c for c in candidates]
        if not passages:
            return []
        pairs = [(query, p) for p in passages]
        scores = self._ce.predict(pairs)
        ranked = sorted(zip(passages, scores), key=lambda t: t[1], reverse=True)
        return ranked[:k]
