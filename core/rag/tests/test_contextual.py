"""Tests for core.rag.python.contextual — uses a fake LLM fn, no network."""

from __future__ import annotations

import sys
from pathlib import Path
from types import SimpleNamespace
from unittest import mock

import pytest

REPO_ROOT = Path(__file__).resolve().parents[3]
sys.path.insert(0, str(REPO_ROOT))

from core.rag import contextualize_chunks, make_openai_llm  # noqa: E402


def test_contextualize_prepends_context_to_each_chunk():
    def llm(prompt: str) -> str:
        # Deterministic fake: the "context" is the first 10 chars of the chunk.
        chunk_line = [line for line in prompt.splitlines() if line and "chunk" not in line.lower()]
        return "CTX-" + chunk_line[-1][:8] if chunk_line else "CTX"

    chunks = ["chunk one content", "chunk two content"]
    out = contextualize_chunks("full document body", chunks, llm)
    assert len(out) == 2
    assert all("\n\n" in c for c in out)
    # Prefix + original content is preserved.
    for original, contextualized in zip(chunks, out):
        assert contextualized.endswith(original)
        assert contextualized.startswith("CTX-")


def test_contextualize_empty_llm_response_falls_back_to_chunk():
    def llm(_: str) -> str:
        return ""  # simulates an LLM that refuses

    out = contextualize_chunks("doc", ["chunk"], llm)
    assert out == ["chunk"]


def test_make_openai_llm_extracts_text_from_response():
    # Stub an OpenAI-compatible client.
    client = mock.MagicMock()
    client.chat.completions.create.return_value = SimpleNamespace(
        choices=[SimpleNamespace(message=SimpleNamespace(content="extracted text"))]
    )
    llm = make_openai_llm(client, "gpt-5-nano")
    assert llm("any prompt") == "extracted text"
    # Verify the client call shape.
    call = client.chat.completions.create.call_args
    assert call.kwargs["model"] == "gpt-5-nano"
    assert call.kwargs["messages"][0]["content"] == "any prompt"


def test_make_openai_llm_handles_none_content():
    client = mock.MagicMock()
    client.chat.completions.create.return_value = SimpleNamespace(
        choices=[SimpleNamespace(message=SimpleNamespace(content=None))]
    )
    llm = make_openai_llm(client, "m")
    assert llm("p") == ""


if __name__ == "__main__":
    sys.exit(pytest.main([__file__, "-v"]))
