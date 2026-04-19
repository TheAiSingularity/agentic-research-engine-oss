"""Mocked tests for research-assistant/production (Wave 2 Tier 2).

Verifies HyDE gating, CoVe parsing, conditional iteration, and
self-consistency selection. No network, no API key, no model.
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

os.environ.setdefault("OPENAI_API_KEY", "test")

# Load THIS recipe's main.py by path, bypassing sys.path / sys.modules
# so the other recipe (beginner/main.py) can't shadow it.
import importlib.util  # noqa: E402

_spec = importlib.util.spec_from_file_location("production_main", Path(__file__).parent / "main.py")
main = importlib.util.module_from_spec(_spec)
_spec.loader.exec_module(main)


def _chat_resp(text: str) -> object:
    return SimpleNamespace(choices=[SimpleNamespace(message=SimpleNamespace(content=text))])


def _searxng_json(hits: list[tuple[str, str, str]]) -> dict:
    return {"results": [{"url": u, "title": t, "content": s} for u, t, s in hits]}


@pytest.fixture
def patched(monkeypatch):
    """Patch OpenAI (prompt-routed), SearXNG HTTP, and core/rag embedder."""
    pass  # main loaded at module top via importlib

    def chat_router(*args, **kwargs):
        p = kwargs.get("messages", [{}])[0].get("content", "")
        if "Break this research question" in p:
            return _chat_resp("sub one\nsub two\nsub three")
        if "concise factual paragraph" in p:
            return _chat_resp("Hypothetical answer text about the topic.")
        if "Summarize these sources" in p:
            return _chat_resp("Search summary with [1] and [2] citations.")
        if "List each standalone factual claim" in p:
            # Two verified, one not — forces iterate.
            return _chat_resp("CLAIM: fact one\nVERIFIED: yes\nCLAIM: fact two\nVERIFIED: no\nCLAIM: fact three\nVERIFIED: yes")
        if "Answer using the evidence" in p:
            return _chat_resp("Final answer [1] with citations [2].")
        return _chat_resp("unexpected prompt")

    client = mock.MagicMock()
    client.chat.completions.create.side_effect = chat_router
    monkeypatch.setattr(main, "OpenAI", mock.MagicMock(return_value=client))

    call_i = {"n": 0}

    def fake_get(url, params=None, timeout=None):
        call_i["n"] += 1
        i = call_i["n"]
        r = mock.MagicMock()
        r.status_code = 200
        r.raise_for_status = mock.MagicMock()
        r.json = lambda: _searxng_json([
            (f"https://a.example/{i}-1", f"A{i}", f"snip A{i}"),
            (f"https://b.example/{i}-2", f"B{i}", f"snip B{i}"),
        ])
        return r

    monkeypatch.setattr(main.requests, "get", fake_get)

    from core.rag import HybridRetriever, Retriever

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

    return client


def test_plan_parses_subqueries_and_skips_hyde_on_numeric(patched, monkeypatch):
    pass  # main loaded at module top via importlib

    monkeypatch.setattr(main, "ENABLE_HYDE", True)
    state = {"question": "How many parameters does Gemma 4 have in 2026?", "iterations": 0}
    result = main._plan(state)
    # Numeric query triggers the gate → no HyDE expansion.
    assert all(s.strip() in ("sub one", "sub two", "sub three") for s in result["subqueries"])


def test_plan_applies_hyde_on_conceptual_query(patched, monkeypatch):
    pass  # main loaded at module top via importlib

    monkeypatch.setattr(main, "ENABLE_HYDE", True)
    state = {"question": "Why does contextual retrieval improve recall?", "iterations": 0}
    result = main._plan(state)
    # HyDE expansion appends a hypothetical paragraph after the raw sub-query.
    assert all("Hypothetical answer" in s for s in result["subqueries"])


def test_plan_skips_hyde_when_disabled(patched, monkeypatch):
    pass  # main loaded at module top via importlib

    monkeypatch.setattr(main, "ENABLE_HYDE", False)
    state = {"question": "Why does contextual retrieval improve recall?", "iterations": 0}
    result = main._plan(state)
    assert not any("Hypothetical" in s for s in result["subqueries"])


def test_verify_parses_cove_and_flags_unverified(patched):
    pass  # main loaded at module top via importlib

    state = {
        "question": "q",
        "answer": "Final answer",
        "evidence": [{"url": "u1", "text": "E1"}, {"url": "u2", "text": "E2"}],
        "iterations": 0,
    }
    result = main._verify(state)
    assert len(result["claims"]) == 3
    assert sum(1 for c in result["claims"] if c["verified"]) == 2
    assert result["unverified"] == ["fact two"]
    assert result["iterations"] == 1


def test_verify_skipped_when_disabled(patched, monkeypatch):
    pass  # main loaded at module top via importlib

    monkeypatch.setattr(main, "ENABLE_VERIFY", False)
    result = main._verify({"question": "q", "answer": "a", "evidence": [], "iterations": 0})
    assert result == {"claims": [], "unverified": []}


def test_after_verify_iterates_when_unverified_and_budget_remaining(patched):
    pass  # main loaded at module top via importlib

    nxt = main._after_verify({"unverified": ["claim"], "iterations": 1})
    assert nxt == "search"


def test_after_verify_ends_when_budget_exhausted(patched, monkeypatch):
    pass  # main loaded at module top via importlib

    monkeypatch.setattr(main, "MAX_ITERATIONS", 2)
    nxt = main._after_verify({"unverified": ["claim"], "iterations": 2})
    assert nxt is main.END


def test_after_verify_ends_when_all_verified(patched):
    pass  # main loaded at module top via importlib

    assert main._after_verify({"unverified": [], "iterations": 0}) is main.END


def test_search_appends_on_iteration_without_duplicating(patched):
    pass  # main loaded at module top via importlib

    # Iteration case: state has evidence + unverified list of claims.
    state = {
        "question": "q",
        "subqueries": ["original sub"],
        "unverified": ["follow-up claim"],
        "evidence": [{"url": "https://a.example/1-1", "title": "A1", "text": "old"}],
        "iterations": 1,
    }
    result = main._search(state)
    # Old evidence preserved; new evidence added without URL collision.
    assert any(e["text"] == "old" for e in result["evidence"])
    assert len(result["evidence"]) >= 2


def test_grounding_score_counts_valid_refs():
    pass  # main loaded at module top via importlib

    ev = [{"url": "a"}, {"url": "b"}, {"url": "c"}]
    # 2/2 valid, sqrt(2) coverage weight
    assert main._grounding_score("claim [1] and [2]", ev) == pytest.approx(2 ** 0.5)
    # 1/2 valid (7 is out of range), sqrt(1) coverage
    assert main._grounding_score("claim [1] and [7]", ev) == pytest.approx(0.5)
    assert main._grounding_score("no citations", ev) == 0.0
    # More valid refs should rank higher at equal validity ratio.
    assert main._grounding_score("a [1][2][3]", ev) > main._grounding_score("b [1]", ev)


def test_synthesize_consistency_picks_best_grounded(patched, monkeypatch):
    pass  # main loaded at module top via importlib

    monkeypatch.setattr(main, "ENABLE_CONSISTENCY", True)
    monkeypatch.setattr(main, "CONSISTENCY_SAMPLES", 3)
    # Stub _synthesize_once to return candidates with varying grounding.
    candidates = iter([
        "weak answer with no citations",
        "ok answer [1]",
        "best answer [1][2][3]",
    ])
    monkeypatch.setattr(main, "_synthesize_once", lambda state: next(candidates))
    result = main._synthesize({"question": "q", "evidence": [{"url": "u1"}, {"url": "u2"}, {"url": "u3"}]})
    assert result["answer"] == "best answer [1][2][3]"


def test_full_graph_with_iteration(patched, monkeypatch):
    """End-to-end with verify flagging → iterate once → end on budget."""
    pass  # main loaded at module top via importlib

    monkeypatch.setattr(main, "MAX_ITERATIONS", 1)
    monkeypatch.setattr(main, "ENABLE_CONSISTENCY", False)
    graph = main.build_graph()
    result = graph.invoke({"question": "Why does contextual retrieval improve recall?", "iterations": 0})
    assert "Final answer" in result["answer"]
    # verify ran at least once; may have iterated once.
    assert result.get("iterations", 0) >= 1


if __name__ == "__main__":
    sys.exit(pytest.main([__file__, "-v"]))
