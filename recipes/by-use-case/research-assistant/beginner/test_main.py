"""Mocked tests for research-assistant/beginner.

No API keys are required — every external client is patched. This verifies
the graph wiring, node contracts, and state shape. For a real end-to-end
check, use `make smoke` after exporting your API keys.
"""

from __future__ import annotations

import os
import sys
from pathlib import Path
from types import SimpleNamespace
from unittest import mock

import pytest

# Make core.rag and main importable.
REPO_ROOT = Path(__file__).resolve().parents[5]
sys.path.insert(0, str(REPO_ROOT))
sys.path.insert(0, str(Path(__file__).parent))

# Fake env so module-level os.environ reads don't fail anywhere.
os.environ.setdefault("GOOGLE_API_KEY", "test")
os.environ.setdefault("EXA_API_KEY", "test")
os.environ.setdefault("OPENAI_API_KEY", "test")


def _fake_gemini_resp(text: str) -> object:
    return SimpleNamespace(text=text)


def _fake_exa_resp(urls_highlights: list[tuple[str, list[str]]]) -> object:
    results = [
        SimpleNamespace(url=u, title=f"title for {u}", highlights=hls)
        for u, hls in urls_highlights
    ]
    return SimpleNamespace(results=results)


def _fake_openai_chat(text: str) -> object:
    return SimpleNamespace(
        choices=[SimpleNamespace(message=SimpleNamespace(content=text))]
    )


@pytest.fixture
def patched_clients(monkeypatch):
    """Patch the three SDK clients main.py imports."""
    import main

    # Planner: Gemini -> 3 sub-queries.
    gemini_client = mock.MagicMock()
    gemini_client.models.generate_content.return_value = _fake_gemini_resp(
        "sub query one\nsub query two\nsub query three"
    )
    monkeypatch.setattr(
        main.genai, "Client", mock.MagicMock(return_value=gemini_client)
    )

    # Search: Exa -> 2 results per query, 1 highlight each.
    exa_client = mock.MagicMock()
    exa_client.search_and_contents.return_value = _fake_exa_resp(
        [
            ("https://a.example/one", ["highlight A"]),
            ("https://b.example/two", ["highlight B"]),
        ]
    )
    monkeypatch.setattr(main, "Exa", mock.MagicMock(return_value=exa_client))

    # Synthesizer: OpenAI -> fixed cited answer.
    openai_client = mock.MagicMock()
    openai_client.chat.completions.create.return_value = _fake_openai_chat(
        "Final answer with [1][2] citations."
    )
    monkeypatch.setattr(
        main, "OpenAI", mock.MagicMock(return_value=openai_client)
    )

    # Retriever: stub the embedder so core/rag doesn't need OpenAI either.
    from core.rag import Retriever

    def fake_embed(batch: list[str]) -> list[list[float]]:
        return [[float(len(s)), float(len(s.split()))] for s in batch]

    original_init = Retriever.__init__

    def patched_init(self, *args, **kwargs):
        original_init(self, *args, **kwargs)
        self.embedder = fake_embed

    monkeypatch.setattr(Retriever, "__init__", patched_init)

    return {"gemini": gemini_client, "exa": exa_client, "openai": openai_client}


def test_plan_parses_three_subqueries(patched_clients):
    import main

    result = main._plan({"question": "anything", "subqueries": [], "evidence": [], "answer": ""})
    assert result["subqueries"] == ["sub query one", "sub query two", "sub query three"]


def test_search_collects_highlights_across_subqueries(patched_clients):
    import main

    state = {"question": "q", "subqueries": ["s1", "s2"], "evidence": [], "answer": ""}
    result = main._search(state)
    # 2 sub-queries × 2 results × 1 highlight = 4 evidence items.
    assert len(result["evidence"]) == 4
    assert all({"url", "title", "text"} <= e.keys() for e in result["evidence"])


def test_retrieve_passes_through_when_few_evidence(patched_clients):
    import main

    evidence = [{"url": "u", "title": "t", "text": "short"}]
    state = {"question": "q", "subqueries": [], "evidence": evidence, "answer": ""}
    result = main._retrieve(state)
    assert result["evidence"] == evidence


def test_retrieve_narrows_when_many_evidence(patched_clients, monkeypatch):
    import main

    monkeypatch.setattr(main, "TOP_K_HIGHLIGHTS", 3)
    evidence = [{"url": f"u{i}", "title": f"t{i}", "text": f"text {i}"} for i in range(10)]
    state = {"question": "query", "subqueries": [], "evidence": evidence, "answer": ""}
    result = main._retrieve(state)
    assert len(result["evidence"]) == 3


def test_synthesize_returns_answer_string(patched_clients):
    import main

    state = {
        "question": "q",
        "subqueries": [],
        "evidence": [{"url": "u", "title": "t", "text": "snippet"}],
        "answer": "",
    }
    result = main._synthesize(state)
    assert "Final answer" in result["answer"]


def test_full_graph_end_to_end(patched_clients):
    import main

    graph = main.build_graph()
    result = graph.invoke(
        {"question": "test", "subqueries": [], "evidence": [], "answer": ""}
    )
    assert result["subqueries"] == ["sub query one", "sub query two", "sub query three"]
    assert len(result["evidence"]) > 0
    assert "Final answer" in result["answer"]


if __name__ == "__main__":
    sys.exit(pytest.main([__file__, "-v"]))
