"""Tests for core.rag.python.rerank.

Patches the lazy CrossEncoder import so the real sentence-transformers
dependency isn't needed to verify correctness of the wiring.
"""

from __future__ import annotations

import sys
from pathlib import Path
from types import SimpleNamespace
from unittest import mock

import pytest

REPO_ROOT = Path(__file__).resolve().parents[3]
sys.path.insert(0, str(REPO_ROOT))

from core.rag import CrossEncoderReranker  # noqa: E402
from core.rag.python import rerank  # noqa: E402


class _FakeCE:
    """Pretends to be sentence-transformers.CrossEncoder.predict()."""

    def __init__(self, scores: list[float]):
        self.scores = scores
        self.calls: list[list[tuple[str, str]]] = []

    def predict(self, pairs):
        self.calls.append(list(pairs))
        return self.scores[: len(pairs)]


def test_rerank_returns_top_k_sorted(monkeypatch):
    ce = _FakeCE([0.1, 0.9, 0.5])
    fake_lazy = SimpleNamespace(predict=ce.predict)
    monkeypatch.setattr(rerank._LazyCrossEncoder, "predict", lambda self, pairs: ce.predict(pairs))

    r = CrossEncoderReranker()
    candidates = [("doc A", 10.0), ("doc B", 9.0), ("doc C", 8.0)]
    top = r.rerank("query", candidates, k=2)
    # Highest score first.
    assert top[0][0] == "doc B"
    assert top[0][1] == pytest.approx(0.9)
    assert top[1][0] == "doc C"


def test_rerank_handles_raw_string_candidates(monkeypatch):
    ce = _FakeCE([0.2, 0.8])
    monkeypatch.setattr(rerank._LazyCrossEncoder, "predict", lambda self, pairs: ce.predict(pairs))

    r = CrossEncoderReranker()
    top = r.rerank("q", ["doc A", "doc B"], k=1)
    assert top[0][0] == "doc B"


def test_rerank_empty_returns_empty():
    r = CrossEncoderReranker()
    assert r.rerank("q", [], k=5) == []


def test_lazy_import_raises_helpful_error(monkeypatch):
    lazy = rerank._LazyCrossEncoder("nonexistent-model")
    # Force the ImportError path.
    monkeypatch.setitem(sys.modules, "sentence_transformers", None)
    with pytest.raises(ImportError, match="sentence-transformers"):
        lazy.predict([("q", "p")])


if __name__ == "__main__":
    sys.exit(pytest.main([__file__, "-v"]))
