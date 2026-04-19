"""Tests for core.rag v0 — uses a mocked embedder so no API key is needed."""

from __future__ import annotations

import sys
from pathlib import Path

import pytest

# Make `core.rag` importable without requiring an install.
REPO_ROOT = Path(__file__).resolve().parents[3]
sys.path.insert(0, str(REPO_ROOT))

from core.rag import Retriever, index, retrieve  # noqa: E402


def fake_embedder(batch: list[str]) -> list[list[float]]:
    """Return a deterministic 3-d embedding: [chars, words, vowels]."""
    out = []
    for s in batch:
        out.append([
            float(len(s)),
            float(len(s.split())),
            float(sum(1 for c in s.lower() if c in "aeiou")),
        ])
    return out


def test_empty_retriever_returns_empty():
    r = Retriever(embedder=fake_embedder)
    assert r.retrieve("anything", k=3) == []


def test_index_and_retrieve_orders_by_similarity():
    docs = [
        "cats are small furry animals",
        "quantum chromodynamics deals with quarks",
        "dogs are medium-sized furry animals",
    ]
    r = index(docs, embedder=fake_embedder)
    results = retrieve("pets that are furry", k=3, retriever=r)
    # All 3 docs come back, sorted by score.
    assert len(results) == 3
    scores = [score for _, score in results]
    assert scores == sorted(scores, reverse=True)


def test_k_clamps_to_corpus_size():
    r = index(["only one doc"], embedder=fake_embedder)
    results = r.retrieve("query", k=10)
    assert len(results) == 1


def test_add_extends_existing_index():
    r = index(["first doc"], embedder=fake_embedder)
    r.add(["second doc"])
    assert len(r.docs) == 2
    assert len(r.vectors) == 2


def test_public_api_exports():
    import core.rag as rag

    assert hasattr(rag, "Retriever")
    assert hasattr(rag, "index")
    assert hasattr(rag, "retrieve")
    assert rag.__version__ == "0.1.0"


if __name__ == "__main__":
    sys.exit(pytest.main([__file__, "-v"]))
