"""Mocked tests for trading-copilot/production — no network, no API keys, no real yfinance."""

from __future__ import annotations

import importlib.util
import os
import sys
from pathlib import Path
from types import SimpleNamespace
from unittest import mock

import pytest

REPO_ROOT = Path(__file__).resolve().parents[5]
sys.path.insert(0, str(REPO_ROOT))
os.environ.setdefault("OPENAI_API_KEY", "test")

_spec = importlib.util.spec_from_file_location("tc_production", Path(__file__).parent / "main.py")
main = importlib.util.module_from_spec(_spec)
_spec.loader.exec_module(main)


def _chat_resp(text: str) -> object:
    return SimpleNamespace(choices=[SimpleNamespace(message=SimpleNamespace(content=text))])


def _searxng_json(hits: list[tuple[str, str, str]]) -> dict:
    return {"results": [{"url": u, "title": t, "content": s} for u, t, s in hits]}


def _fake_snapshot(ticker: str) -> dict:
    return {
        "ticker": ticker, "last": 100.0, "pct_change_1d": -1.5,
        "sma50": 95.0, "sma200": 105.0, "rsi14": 28.0,
        "closes_tail": [101.0, 100.5, 100.2, 100.1, 100.0],
    }


@pytest.fixture
def patched(monkeypatch, tmp_path):
    """Route LLM calls by prompt substring; stub SearXNG + yfinance + config path."""

    def chat_router(*args, **kwargs):
        p = kwargs.get("messages", [{}])[0].get("content", "")
        if "market analyst" in p:
            if "AAPL" in p:
                return _chat_resp("CANDIDATE: rsi_oversold | severity=med | RSI below 30 and -1.5% today.")
            return _chat_resp("")
        if "step-level verifier" in p:
            return _chat_resp("VERDICT: accept\nFEEDBACK: ")
        if "candidate alert was produced" in p:
            return _chat_resp("VERDICT: keep\nREASON: RSI and pct_change agree with the claim.")
        if "list each atomic factual claim" in p:
            return _chat_resp("CLAIM: RSI is below 30\nSUPPORTED: yes\n"
                              "CLAIM: Stock dropped today\nSUPPORTED: yes")
        return _chat_resp("")

    client = mock.MagicMock()
    client.chat.completions.create.side_effect = chat_router
    monkeypatch.setattr(main.beginner, "OpenAI", mock.MagicMock(return_value=client))

    def fake_get(url, params=None, timeout=None):
        r = mock.MagicMock()
        r.status_code = 200
        r.raise_for_status = mock.MagicMock()
        t = (params or {}).get("q", "X").split()[0]
        r.json = lambda: _searxng_json([
            (f"https://n.example/{t}-1", f"{t} news A", "snippet A"),
            (f"https://n.example/{t}-2", f"{t} news B", "snippet B"),
        ])
        return r

    monkeypatch.setattr(main.beginner.requests, "get", fake_get)
    monkeypatch.setattr(main.beginner, "_fetch_prices", _fake_snapshot)
    main.beginner._price_cache.clear()

    cfg = tmp_path / "watchlist.yaml"
    cfg.write_text(
        "watchlist: [AAPL, NVDA]\n"
        "rules:\n"
        "  - kind: rsi_oversold\n"
        "    threshold: 30\n"
    )
    monkeypatch.setattr(main.beginner, "WATCHLIST_FILE", str(cfg))
    return client


# ── T4.1 step critic ──────────────────────────────────────────────────

def test_critic_accepts_when_disabled(patched, monkeypatch):
    monkeypatch.setattr(main, "ENABLE_STEP_VERIFY", False)
    accept, fb = main._critic("gather", "any", "ctx")
    assert accept is True and fb == ""


def test_critic_parses_verdict(patched):
    accept, _ = main._critic("gather", "payload", "ctx")
    assert accept is True


def test_critic_parses_redo_verdict(patched, monkeypatch):
    def redo(*args, **kwargs):
        return _chat_resp("VERDICT: redo\nFEEDBACK: news is sparse")

    client = mock.MagicMock()
    client.chat.completions.create.side_effect = redo
    monkeypatch.setattr(main.beginner, "OpenAI", mock.MagicMock(return_value=client))
    accept, fb = main._critic("gather", "p", "c")
    assert accept is False
    assert fb == "news is sparse"


# ── Gather extensions ─────────────────────────────────────────────────

def test_gather_includes_social_when_enabled(patched, monkeypatch):
    monkeypatch.setattr(main, "ENABLE_SOCIAL", True)
    # Social fetcher stub — no PRAW creds → returns empty list.
    monkeypatch.setattr(main, "_fetch_social", lambda t: [{"source": "r/wsb", "title": f"{t} moon"}])
    state = {"watchlist": ["AAPL"], "rules": []}
    result = main._gather(state)
    assert "social" in result
    assert result["social"]["AAPL"][0]["title"] == "AAPL moon"


def test_gather_skips_social_when_disabled(patched, monkeypatch):
    monkeypatch.setattr(main, "ENABLE_SOCIAL", False)
    state = {"watchlist": ["AAPL"], "rules": []}
    result = main._gather(state)
    assert result["social"] == {}


def test_gather_critic_records_feedback(patched, monkeypatch):
    def redo(*args, **kwargs):
        return _chat_resp("VERDICT: redo\nFEEDBACK: too few news items")

    client = mock.MagicMock()
    client.chat.completions.create.side_effect = redo
    monkeypatch.setattr(main.beginner, "OpenAI", mock.MagicMock(return_value=client))
    state = {"watchlist": ["AAPL"], "prices": {"AAPL": _fake_snapshot("AAPL")}, "news": {"AAPL": []}}
    result = main._gather_critic(state)
    assert result["critic_notes"] == ["gather: too few news items"]


# ── Self-consistency skeptic ──────────────────────────────────────────

def test_skeptic_vote_n1_when_consistency_disabled(patched, monkeypatch):
    monkeypatch.setattr(main, "ENABLE_CONSISTENCY", False)
    c = {"ticker": "AAPL", "rule_fired": "rsi_oversold", "severity": "med", "reasoning": "oversold"}
    state = {"prices": {"AAPL": _fake_snapshot("AAPL")}, "news": {"AAPL": []}}
    result = main._skeptic({**state, "candidates": [c]})
    # n=1 — single sample, kept.
    assert len(result["alerts"]) == 1
    assert result["alerts"][0]["vote_detail"]["n"] == 1


def test_skeptic_majority_vote_keeps(patched, monkeypatch):
    monkeypatch.setattr(main, "ENABLE_CONSISTENCY", True)
    monkeypatch.setattr(main, "CONSISTENCY_SAMPLES", 3)
    c = {"ticker": "AAPL", "rule_fired": "rsi_oversold",
         "severity": "low", "reasoning": "RSI below 30 and -1.5% on the day is a longer reason"}
    state = {"prices": {"AAPL": _fake_snapshot("AAPL")}, "news": {"AAPL": []}}
    result = main._skeptic({**state, "candidates": [c]})
    # All 3 votes are "keep" per the fixture → majority keep.
    assert len(result["alerts"]) == 1
    assert result["alerts"][0]["vote_detail"] == {"n": 3, "kept": 3}


def test_skeptic_majority_vote_drops(patched, monkeypatch):
    monkeypatch.setattr(main, "ENABLE_CONSISTENCY", True)
    monkeypatch.setattr(main, "CONSISTENCY_SAMPLES", 3)

    calls = {"n": 0}

    def mixed(*args, **kwargs):
        p = kwargs.get("messages", [{}])[0].get("content", "")
        if "candidate alert was produced" in p:
            calls["n"] += 1
            if calls["n"] == 1:
                return _chat_resp("VERDICT: keep\nREASON: close call")
            return _chat_resp("VERDICT: drop\nREASON: unsupported")
        return _chat_resp("")

    client = mock.MagicMock()
    client.chat.completions.create.side_effect = mixed
    monkeypatch.setattr(main.beginner, "OpenAI", mock.MagicMock(return_value=client))
    c = {"ticker": "AAPL", "rule_fired": "r", "severity": "low",
         "reasoning": "some lengthy reasoning that triggers 3-sample vote"}
    result = main._skeptic({"candidates": [c], "prices": {"AAPL": _fake_snapshot("AAPL")}, "news": {"AAPL": []}})
    assert result["alerts"] == []  # majority dropped


def test_skeptic_adaptive_n1_for_high_severity_short(patched, monkeypatch):
    monkeypatch.setattr(main, "ENABLE_CONSISTENCY", True)
    monkeypatch.setattr(main, "CONSISTENCY_SAMPLES", 3)
    c = {"ticker": "AAPL", "rule_fired": "r", "severity": "high", "reasoning": "short clear."}
    state = {"prices": {"AAPL": _fake_snapshot("AAPL")}, "news": {"AAPL": []}}
    result = main._skeptic({**state, "candidates": [c]})
    assert result["alerts"][0]["vote_detail"]["n"] == 1


# ── CoVe verify_alerts ────────────────────────────────────────────────

def test_verify_alerts_keeps_fully_supported(patched):
    state = {
        "alerts": [{"ticker": "AAPL", "rule_fired": "r", "severity": "med",
                    "reasoning": "RSI below 30 and price drop", "verdict": "v"}],
        "prices": {"AAPL": _fake_snapshot("AAPL")},
        "news": {"AAPL": []},
    }
    result = main._verify_alerts(state)
    assert len(result["verified_alerts"]) == 1
    assert result["verified_alerts"][0]["n_claims"] == 2


def test_verify_alerts_drops_unsupported(patched, monkeypatch):
    def no_support(*args, **kwargs):
        p = kwargs.get("messages", [{}])[0].get("content", "")
        if "list each atomic factual claim" in p:
            return _chat_resp("CLAIM: RSI is below 30\nSUPPORTED: yes\n"
                              "CLAIM: earnings beat estimates\nSUPPORTED: no")
        return _chat_resp("")

    client = mock.MagicMock()
    client.chat.completions.create.side_effect = no_support
    monkeypatch.setattr(main.beginner, "OpenAI", mock.MagicMock(return_value=client))
    state = {
        "alerts": [{"ticker": "AAPL", "rule_fired": "r", "severity": "med",
                    "reasoning": "oversold + earnings", "verdict": "v"}],
        "prices": {"AAPL": _fake_snapshot("AAPL")},
        "news": {"AAPL": []},
    }
    result = main._verify_alerts(state)
    assert result["verified_alerts"] == []


def test_verify_alerts_passes_through_when_disabled(patched, monkeypatch):
    monkeypatch.setattr(main, "ENABLE_VERIFY", False)
    alerts = [{"ticker": "AAPL", "rule_fired": "r", "severity": "med",
               "reasoning": "x", "verdict": "v"}]
    result = main._verify_alerts({"alerts": alerts, "prices": {}, "news": {}})
    assert result["verified_alerts"] == alerts


# ── Full graph e2e ────────────────────────────────────────────────────

def test_full_graph_end_to_end(patched, capsys):
    result = main.build_graph().invoke({})
    assert set(result["watchlist"]) == {"AAPL", "NVDA"}
    assert len(result["candidates"]) == 1
    assert len(result["alerts"]) == 1
    assert len(result["verified_alerts"]) == 1
    assert len(result["routed"]) == 1
    assert "[stdout-alert]" in capsys.readouterr().out


# ── Safety rail ───────────────────────────────────────────────────────

def test_no_execution_symbols_in_production_main():
    src = (Path(__file__).parent / "main.py").read_text().lower()
    for token in ("place_order", "submit_order", "cancel_order", "buy_stock",
                  "sell_stock", "execute_trade", "broker.",
                  "alpaca", "ib_insync", "interactive_brokers"):
        assert token not in src, f"forbidden symbol `{token}` in production/main.py"


if __name__ == "__main__":
    sys.exit(pytest.main([__file__, "-v"]))
