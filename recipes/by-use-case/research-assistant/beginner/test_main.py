"""Mocked tests for research-assistant/beginner (portable stack).

No API key or network needed — OpenAI client and SearXNG HTTP are patched.
For a real live check, use `make smoke` after starting Ollama/vLLM + SearXNG.
"""

from __future__ import annotations

import os
import sys
from pathlib import Path
from types import SimpleNamespace
from unittest import mock

import pytest

REPO_ROOT = Path(__file__).resolve().parents[5]
sys.path.insert(0, str(REPO_ROOT))
sys.path.insert(0, str(Path(__file__).parent))

os.environ.setdefault("OPENAI_API_KEY", "test")


def _chat_resp(text: str) -> object:
    return SimpleNamespace(choices=[SimpleNamespace(message=SimpleNamespace(content=text))])


def _searxng_json(hits: list[tuple[str, str, str]]) -> dict:
    """[(url, title, snippet), ...] → SearXNG-shaped JSON."""
    return {"results": [{"url": u, "title": t, "content": s} for u, t, s in hits]}


@pytest.fixture
def patched(monkeypatch):
    """Patch OpenAI client (routed by prompt content) and SearXNG HTTP."""
    import main

    def chat_router(*args, **kwargs):
        prompt = kwargs.get("messages", [{}])[0].get("content", "")
        if "Break this research question" in prompt:
            return _chat_resp("sub one\nsub two\nsub three")
        if "Summarize these sources" in prompt:
            return _chat_resp("Summary with [1] and [2] citations.")
        return _chat_resp("Final answer with [1][2] citations.")

    client = mock.MagicMock()
    client.chat.completions.create.side_effect = chat_router
    monkeypatch.setattr(main, "OpenAI", mock.MagicMock(return_value=client))

    # SearXNG JSON response — unique URLs per sub-query so dedup doesn't collapse them.
    call_count = {"n": 0}

    def fake_get(url, params=None, timeout=None):
        call_count["n"] += 1
        i = call_count["n"]
        r = mock.MagicMock()
        r.status_code = 200
        r.raise_for_status = mock.MagicMock()
        r.json = lambda: _searxng_json([
            (f"https://a.example/{i}-1", f"Title A-{i}", f"snippet A-{i}"),
            (f"https://b.example/{i}-2", f"Title B-{i}", f"snippet B-{i}"),
        ])
        return r

    monkeypatch.setattr(main.requests, "get", fake_get)

    # Stub embedder on both v0 Retriever and v1 HybridRetriever so no network is hit.
    from core.rag import HybridRetriever, Retriever

    def fake_embed(batch):
        return [[float(len(s)), float(len(s.split()))] for s in batch]

    for cls in (Retriever, HybridRetriever):
        original_init = cls.__init__

        def make_patched(orig):
            def patched_init(self, *args, **kwargs):
                orig(self, *args, **kwargs)
                self.embedder = fake_embed

            return patched_init

        monkeypatch.setattr(cls, "__init__", make_patched(original_init))

    return client


def test_plan_parses_subqueries(patched):
    import main

    result = main._plan({"question": "q", "subqueries": [], "evidence": [], "answer": ""})
    assert result["subqueries"] == ["sub one", "sub two", "sub three"]


def test_searxng_hits_parsed(patched):
    import main

    hits = main._searxng("anything")
    assert len(hits) == 2
    assert hits[0]["url"].startswith("https://a.example/")
    assert set(hits[0].keys()) == {"url", "title", "snippet"}


def test_search_collects_summaries(patched):
    state = {"question": "q", "subqueries": ["s1", "s2"], "evidence": [], "answer": ""}
    import main

    result = main._search(state)
    # 2 sub-queries × 2 hits each = 4 evidence items. Each text is the summary.
    assert len(result["evidence"]) == 4
    assert all(e["text"].startswith("Summary with") for e in result["evidence"])


def test_search_empty_hits(patched, monkeypatch):
    import main

    def empty_get(url, params=None, timeout=None):
        r = mock.MagicMock()
        r.status_code = 200
        r.raise_for_status = mock.MagicMock()
        r.json = lambda: {"results": []}
        return r

    monkeypatch.setattr(main.requests, "get", empty_get)
    state = {"question": "q", "subqueries": ["only"], "evidence": [], "answer": ""}
    assert main._search(state)["evidence"] == []


def test_retrieve_passes_through_when_few_evidence(patched):
    import main

    evidence = [{"url": "u", "title": "t", "text": "short"}]
    state = {"question": "q", "subqueries": [], "evidence": evidence, "answer": ""}
    assert main._retrieve(state)["evidence"] == evidence


def test_retrieve_narrows_when_many_evidence(patched, monkeypatch):
    import main

    monkeypatch.setattr(main, "TOP_K_EVIDENCE", 3)
    evidence = [{"url": f"u{i}", "title": f"t{i}", "text": f"text {i}"} for i in range(10)]
    state = {"question": "query", "subqueries": [], "evidence": evidence, "answer": ""}
    assert len(main._retrieve(state)["evidence"]) == 3


def test_synthesize_returns_answer_string(patched):
    import main

    state = {"question": "q", "subqueries": [], "evidence": [{"url": "u", "title": "t", "text": "snippet"}], "answer": ""}
    assert "Final answer" in main._synthesize(state)["answer"]


def test_full_graph_end_to_end(patched):
    import main

    result = main.build_graph().invoke({"question": "test", "subqueries": [], "evidence": [], "answer": ""})
    assert result["subqueries"] == ["sub one", "sub two", "sub three"]
    assert len(result["evidence"]) > 0
    assert "Final answer" in result["answer"]


if __name__ == "__main__":
    sys.exit(pytest.main([__file__, "-v"]))
