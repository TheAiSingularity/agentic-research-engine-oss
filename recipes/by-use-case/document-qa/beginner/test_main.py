"""Mocked tests for document-qa/beginner.

No network, no API keys, no real LLM calls. The core/rag pieces use a
fake embedder; the OpenAI client is a MagicMock whose chat_router returns
canned responses based on prompt patterns.
"""

from __future__ import annotations

import os
import sys
from pathlib import Path
from types import SimpleNamespace
from unittest import mock

import pytest

REPO_ROOT = Path(__file__).resolve().parents[4]
sys.path.insert(0, str(REPO_ROOT))

os.environ.setdefault("OPENAI_API_KEY", "test")

import importlib.util  # noqa: E402

_spec = importlib.util.spec_from_file_location("docqa_main", Path(__file__).parent / "main.py")
main = importlib.util.module_from_spec(_spec)
_spec.loader.exec_module(main)


def _chat_resp(text: str) -> object:
    return SimpleNamespace(choices=[SimpleNamespace(message=SimpleNamespace(content=text))])


@pytest.fixture
def patched(monkeypatch, tmp_path):
    """Patch OpenAI client + core.rag embedder; disable streaming by default."""

    def chat_router(*args, **kwargs):
        p = kwargs.get("messages", [{}])[0].get("content", "")
        if "Answer the question using ONLY the evidence" in p:
            return _chat_resp("Hybrid retrieval combines BM25 and dense [1].")
        if "List each standalone factual claim" in p:
            return _chat_resp("CLAIM: Hybrid combines BM25 and dense\nVERIFIED: yes")
        return _chat_resp("unexpected prompt")

    client = mock.MagicMock()
    client.chat.completions.create.side_effect = chat_router
    monkeypatch.setattr(main, "OpenAI", mock.MagicMock(return_value=client))

    # Patch core.rag embedders so no network is touched for embeddings.
    from core.rag import HybridRetriever
    from core.rag.python.rag import Retriever

    def fake_embed(batch):
        return [[float(len(s)), float(len(s.split()))] for s in batch]

    for cls in (Retriever, HybridRetriever):
        original = cls.__init__

        def make_patched(orig):
            def patched_init(self, *args, **kwargs):
                orig(self, *args, **kwargs)
                self.embedder = fake_embed

            return patched_init

        monkeypatch.setattr(cls, "__init__", make_patched(original))

    # Streaming path uses stream=True which the mock doesn't produce → force batched.
    monkeypatch.setattr(main, "ENABLE_STREAM", False)
    return client


# ── Node-level behavior ──────────────────────────────────────────────

def test_load_corpus_builds_from_docs_dir(patched, monkeypatch, tmp_path):
    (tmp_path / "a.md").write_text("First doc content about cats.\n\nSecond para about dogs.")
    monkeypatch.setattr(main, "DOCS_DIR", str(tmp_path))
    monkeypatch.setattr(main, "CORPUS_PATH", "")
    result = main._load_corpus({"question": "q"})
    idx = result["corpus"]
    assert len(idx.chunks) == 2
    assert {c.source for c in idx.chunks} == {"a.md"}


def test_load_corpus_loads_from_prebuilt_path(patched, monkeypatch, tmp_path):
    # Build and save an index, then load it via CORPUS_PATH.
    from core.rag import CorpusIndex
    (tmp_path / "src").mkdir()
    (tmp_path / "src" / "note.md").write_text("Content about RAG.")
    built = CorpusIndex.build(tmp_path / "src")
    out = tmp_path / "built.idx"
    built.save(out)

    monkeypatch.setattr(main, "DOCS_DIR", "")
    monkeypatch.setattr(main, "CORPUS_PATH", str(out))
    result = main._load_corpus({"question": "q"})
    assert len(result["corpus"].chunks) == 1


def test_load_corpus_errors_when_nothing_configured(patched, monkeypatch):
    monkeypatch.setattr(main, "DOCS_DIR", "")
    monkeypatch.setattr(main, "CORPUS_PATH", "")
    with pytest.raises(RuntimeError, match="DOCS_DIR"):
        main._load_corpus({"question": "q"})


def test_retrieve_shapes_corpus_urls_with_page_and_chunk(patched, tmp_path):
    (tmp_path / "a.md").write_text("Alpha content.\n\nBeta content.")
    (tmp_path / "b.md").write_text("Gamma content.")
    from core.rag import CorpusIndex
    idx = CorpusIndex.build(tmp_path)
    result = main._retrieve({"question": "content", "corpus": idx})
    assert result["hits"]
    for h in result["hits"]:
        assert h["url"].startswith("corpus://")
        assert "#c" in h["url"]


def test_synthesize_with_hits_produces_cited_answer(patched):
    state = {
        "question": "what is hybrid?",
        "hits": [{"url": "corpus://a.md#c0", "text": "Hybrid combines BM25 + dense."}],
    }
    result = main._synthesize(state)
    assert "[1]" in result["answer"]


def test_synthesize_with_empty_hits_returns_no_chunks_message(patched):
    result = main._synthesize({"question": "q", "hits": []})
    assert "No relevant chunks" in result["answer"]


def test_verify_parses_claims_and_counts_verified(patched):
    state = {
        "question": "q",
        "answer": "Hybrid combines BM25 and dense [1].",
        "hits": [{"url": "corpus://a.md#c0", "text": "Hybrid retrieval combines BM25 + dense."}],
    }
    result = main._verify(state)
    assert len(result["claims"]) == 1
    assert result["verified_count"] == 1


def test_verify_skipped_when_disabled(patched, monkeypatch):
    monkeypatch.setattr(main, "ENABLE_VERIFY", False)
    result = main._verify({"question": "q", "answer": "something", "hits": []})
    assert result == {"claims": [], "verified_count": 0}


# ── Full-graph integration ───────────────────────────────────────────

def test_full_graph_end_to_end(patched, monkeypatch, tmp_path):
    (tmp_path / "doc.md").write_text(
        "# Retrieval\n\n"
        "Hybrid retrieval combines BM25 and dense embeddings using RRF.\n\n"
        "Cross-encoder reranking is a second stage."
    )
    monkeypatch.setattr(main, "DOCS_DIR", str(tmp_path))
    monkeypatch.setattr(main, "CORPUS_PATH", "")
    graph = main.build_graph()
    result = graph.invoke({"question": "What does hybrid retrieval combine?"})
    assert "BM25" in result["answer"] or "dense" in result["answer"]
    assert result["hits"]
    assert result["verified_count"] >= 1


# ── Safety / correctness ─────────────────────────────────────────────

def test_no_web_search_symbols_in_main():
    """document-qa is corpus-only; it must NOT reach out to the web at runtime.

    Scans only executable lines (skips the module docstring) so that safety
    copy referencing `searxng` / `requests.get` in prose doesn't false-positive.
    """
    import ast
    src_text = (Path(__file__).parent / "main.py").read_text()
    tree = ast.parse(src_text)
    # Strip the module docstring before serializing back to code-only text.
    if tree.body and isinstance(tree.body[0], ast.Expr) and isinstance(tree.body[0].value, ast.Constant):
        tree.body = tree.body[1:]
    code_only = ast.unparse(tree).lower()
    for token in ("searxng", "trafilatura.fetch_url", "requests.get", "webhook"):
        assert token not in code_only, f"unexpected web-reach symbol `{token}` in document-qa/main.py"


if __name__ == "__main__":
    sys.exit(pytest.main([__file__, "-v"]))
