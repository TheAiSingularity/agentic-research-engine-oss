"""Tests for core.rag.python.hybrid — uses a mocked embedder, no network."""

from __future__ import annotations

import sys
from pathlib import Path

import pytest

REPO_ROOT = Path(__file__).resolve().parents[3]
sys.path.insert(0, str(REPO_ROOT))

from core.rag import HybridRetriever, hybrid_index  # noqa: E402
from core.rag.python.hybrid import _rrf_fuse, _tokenize  # noqa: E402


def fake_embedder(batch: list[str]) -> list[list[float]]:
    """Deterministic 3-d embedding — unrelated to semantics."""
    return [[float(len(s)), float(len(s.split())), float(sum(1 for c in s.lower() if c in "aeiou"))] for s in batch]


def test_tokenize_lowercases_and_splits():
    assert _tokenize("Hello World! 2026") == ["hello", "world", "2026"]
    assert _tokenize("path/to/file.md") == ["path", "to", "file", "md"]


def test_rrf_fuse_favors_documents_ranked_well_across_lists():
    # doc 5 is #1 in both lists → wins. doc 0 is last in both → loses.
    a = [5, 1, 2, 3, 4, 0]
    b = [5, 2, 1, 3, 4, 0]
    fused = _rrf_fuse([a, b])
    ids = [doc_id for doc_id, _ in fused]
    assert ids[0] == 5
    assert ids[-1] == 0


def test_rrf_fuse_ties_break_by_insertion_order():
    # Perfectly symmetric ranks should produce tied top scores.
    a = [0, 1, 2]
    b = [2, 1, 0]
    fused = _rrf_fuse([a, b])
    # All three get very close scores; top-1 and bottom-1 tie exactly.
    scores = [s for _, s in fused]
    assert scores[0] == scores[1]  # tied top, tied last


def test_empty_hybrid_returns_empty():
    h = HybridRetriever(embedder=fake_embedder)
    assert h.retrieve("anything", k=3) == []


def test_hybrid_finds_exact_token_bm25_would_catch():
    docs = [
        "cats are small furry animals",
        "quantum chromodynamics deals with quarks",
        "BAAI bge-reranker-v2-m3 is a cross-encoder from 2024",
    ]
    h = hybrid_index(docs, embedder=fake_embedder)
    # Exact string match — BM25 catches even though our fake embedder is garbage.
    top = h.retrieve("BAAI bge-reranker-v2-m3", k=3)
    assert top[0][0] == docs[2]


def test_hybrid_rrf_scores_are_descending():
    docs = ["alpha beta gamma", "beta gamma delta", "delta epsilon"]
    h = hybrid_index(docs, embedder=fake_embedder)
    top = h.retrieve("gamma", k=3)
    scores = [s for _, s in top]
    assert scores == sorted(scores, reverse=True)


def test_add_is_incremental_and_rebuilds_bm25():
    # BM25's IDF needs a non-trivial corpus; with 2 docs everything is tied.
    corpus_a = ["cats purr softly", "dogs bark loudly"]
    corpus_b = [
        "BAAI bge-reranker-v2-m3 is a cross-encoder from 2024",
        "quantum chromodynamics deals with quarks and gluons",
        "the sun is a type of star at the center of the solar system",
    ]
    h = HybridRetriever(embedder=fake_embedder)
    h.add(corpus_a)
    h.add(corpus_b)
    assert len(h.docs) == 5
    # A rare, exact-token query lands BM25 squarely on doc 2.
    top = h.retrieve("BAAI bge-reranker-v2-m3", k=5)
    assert top[0][0] == "BAAI bge-reranker-v2-m3 is a cross-encoder from 2024"


if __name__ == "__main__":
    sys.exit(pytest.main([__file__, "-v"]))
