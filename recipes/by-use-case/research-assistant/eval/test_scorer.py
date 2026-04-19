"""Unit tests for the pure helper functions in scorer.py (no network)."""

from __future__ import annotations

import os
import sys
from pathlib import Path

import pytest

os.environ.setdefault("OPENAI_API_KEY", "test")
sys.path.insert(0, str(Path(__file__).resolve().parents[5]))
sys.path.insert(0, str(Path(__file__).parent.parent / "beginner"))
sys.path.insert(0, str(Path(__file__).parent))

from scorer import _citation_accuracy, _citation_precision, _estimate_tokens


def test_citation_precision_all_required_domains_present():
    ans = "Answer [1] from https://anthropic.com/x and also https://exa.ai/y [2]."
    assert _citation_precision(ans, ["anthropic.com", "exa.ai"]) == 1.0


def test_citation_precision_partial():
    ans = "Just https://anthropic.com/x is cited."
    assert _citation_precision(ans, ["anthropic.com", "exa.ai"]) == 0.5


def test_citation_precision_empty_requirements_is_perfect():
    assert _citation_precision("no urls here", []) == 1.0


def test_citation_accuracy_all_valid():
    evidence = [{"url": "a", "text": "A"}, {"url": "b", "text": "B"}, {"url": "c", "text": "C"}]
    ans = "Claim [1] and claim [2] and claim [3]."
    assert _citation_accuracy(ans, evidence) == 1.0


def test_citation_accuracy_detects_hallucinated_ref():
    evidence = [{"url": "a", "text": "A"}, {"url": "b", "text": "B"}]
    ans = "Claim [1] and claim [7]."  # [7] out of range
    assert _citation_accuracy(ans, evidence) == 0.5


def test_citation_accuracy_no_citations_is_perfect():
    assert _citation_accuracy("just a plain answer", [{"url": "a"}]) == 1.0


def test_estimate_tokens_rough_rule():
    assert _estimate_tokens("a" * 40) == 10
    assert _estimate_tokens("") >= 1  # floor at 1


if __name__ == "__main__":
    sys.exit(pytest.main([__file__, "-v"]))
