"""Mocked tests for trading-copilot/beginner — no network, no API keys, no real yfinance."""

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

_spec = importlib.util.spec_from_file_location("trading_main", Path(__file__).parent / "main.py")
main = importlib.util.module_from_spec(_spec)
_spec.loader.exec_module(main)


def _chat_resp(text: str) -> object:
    return SimpleNamespace(choices=[SimpleNamespace(message=SimpleNamespace(content=text))])


def _searxng_json(hits: list[tuple[str, str, str]]) -> dict:
    return {"results": [{"url": u, "title": t, "content": s} for u, t, s in hits]}


def _fake_snapshot(ticker: str) -> dict:
    """Realistic-shaped price snapshot used by the mocked _fetch_prices."""
    return {
        "ticker": ticker, "last": 100.0, "pct_change_1d": -1.5,
        "sma50": 95.0, "sma200": 105.0, "rsi14": 28.0,
        "closes_tail": [101.0, 100.5, 100.2, 100.1, 100.0],
    }


@pytest.fixture
def patched(monkeypatch, tmp_path):
    """Patch OpenAI (prompt-routed), SearXNG HTTP, yfinance, and file-system config."""

    def chat_router(*args, **kwargs):
        p = kwargs.get("messages", [{}])[0].get("content", "")
        if "market analyst" in p:
            # Analyst — emit one candidate for AAPL rsi_oversold, none for the others.
            if "AAPL" in p:
                return _chat_resp("CANDIDATE: rsi_oversold | severity=med | RSI below 30 and -1.5% on the day.")
            return _chat_resp("")
        if "candidate alert was produced" in p:
            return _chat_resp("VERDICT: keep\nREASON: RSI and pct_change agree with the claim.")
        return _chat_resp("")

    client = mock.MagicMock()
    client.chat.completions.create.side_effect = chat_router
    monkeypatch.setattr(main, "OpenAI", mock.MagicMock(return_value=client))

    def fake_get(url, params=None, timeout=None):
        r = mock.MagicMock()
        r.status_code = 200
        r.raise_for_status = mock.MagicMock()
        t = (params or {}).get("q", "X").split()[0]
        r.json = lambda: _searxng_json([
            (f"https://news.example/{t}-1", f"{t} earnings beat", f"snippet about {t}"),
            (f"https://news.example/{t}-2", f"{t} partners with X", f"more {t} context"),
        ])
        return r

    monkeypatch.setattr(main.requests, "get", fake_get)
    monkeypatch.setattr(main, "_fetch_prices", _fake_snapshot)
    # Isolate price cache (would leak between tests otherwise).
    main._price_cache.clear()

    # Isolate config file.
    cfg = tmp_path / "watchlist.yaml"
    cfg.write_text(
        "watchlist: [AAPL, NVDA]\n"
        "rules:\n"
        "  - kind: sma_cross\n"
        "    fast: 50\n"
        "    slow: 200\n"
        "  - kind: rsi_oversold\n"
        "    window: 14\n"
        "    threshold: 30\n"
    )
    monkeypatch.setattr(main, "WATCHLIST_FILE", str(cfg))
    return client


# ── Node contracts ────────────────────────────────────────────────────

def test_load_config_reads_yaml(patched):
    result = main._load_config({})
    assert result["watchlist"] == ["AAPL", "NVDA"]
    assert len(result["rules"]) == 2


def test_load_config_passthrough_when_state_has_watchlist(patched):
    # If state already has both, no file I/O.
    result = main._load_config({"watchlist": ["X"], "rules": [{"kind": "k"}]})
    assert result == {}


def test_load_config_uppercases_and_filters_invalid_tickers(patched, tmp_path):
    cfg = tmp_path / "bad.yaml"
    cfg.write_text("watchlist: [aapl, 'A!!!', 'NVDA  ']\nrules: []\n")
    main.WATCHLIST_FILE = str(cfg)
    out = main._load_config({})
    # 'A!!!' is non-alnum → dropped; others normalized to uppercase.
    assert out["watchlist"] == ["AAPL", "NVDA"]


def test_gather_populates_prices_and_news(patched):
    state = {"watchlist": ["AAPL", "NVDA"], "rules": []}
    result = main._gather(state)
    assert set(result["prices"]) == {"AAPL", "NVDA"}
    assert result["prices"]["AAPL"]["last"] == 100.0
    assert len(result["news"]["AAPL"]) == 2


def test_analyze_emits_candidate_for_matching_ticker(patched):
    state = {
        "watchlist": ["AAPL", "NVDA"],
        "rules": [{"kind": "rsi_oversold"}],
        "prices": {"AAPL": _fake_snapshot("AAPL"), "NVDA": _fake_snapshot("NVDA")},
        "news": {"AAPL": [{"title": "earnings beat"}], "NVDA": [{"title": "stable day"}]},
    }
    result = main._analyze(state)
    assert len(result["candidates"]) == 1
    c = result["candidates"][0]
    assert c["ticker"] == "AAPL"
    assert c["rule_fired"] == "rsi_oversold"
    assert c["severity"] == "med"
    assert "RSI" in c["reasoning"]


def test_analyze_skips_tickers_with_error_snapshot(patched):
    state = {
        "watchlist": ["AAPL"],
        "rules": [{"kind": "rsi_oversold"}],
        "prices": {"AAPL": {"ticker": "AAPL", "error": "no data"}},
        "news": {"AAPL": []},
    }
    assert main._analyze(state)["candidates"] == []


def test_skeptic_keeps_approved_candidate(patched):
    state = {
        "candidates": [{"ticker": "AAPL", "rule_fired": "rsi_oversold",
                        "severity": "med", "reasoning": "oversold"}],
        "prices": {"AAPL": _fake_snapshot("AAPL")},
        "news": {"AAPL": []},
    }
    result = main._skeptic(state)
    assert len(result["alerts"]) == 1
    assert result["alerts"][0]["verdict"]


def test_skeptic_drops_rejected_candidate(patched, monkeypatch):
    def reject_router(*args, **kwargs):
        p = kwargs.get("messages", [{}])[0].get("content", "")
        if "candidate alert was produced" in p:
            return _chat_resp("VERDICT: drop\nREASON: data doesn't support the claim.")
        return _chat_resp("")

    client = mock.MagicMock()
    client.chat.completions.create.side_effect = reject_router
    monkeypatch.setattr(main, "OpenAI", mock.MagicMock(return_value=client))
    state = {
        "candidates": [{"ticker": "AAPL", "rule_fired": "r", "severity": "low", "reasoning": "x"}],
        "prices": {"AAPL": _fake_snapshot("AAPL")},
        "news": {"AAPL": []},
    }
    assert main._skeptic(state)["alerts"] == []


def test_skeptic_no_ops_on_empty_candidates(patched):
    assert main._skeptic({"candidates": [], "prices": {}, "news": {}}) == {"alerts": []}


# ── Alert routing ─────────────────────────────────────────────────────

def test_router_prints_to_stdout_when_no_webhook(patched, capsys):
    state = {"alerts": [{"ticker": "AAPL", "rule_fired": "rsi_oversold",
                         "severity": "med", "reasoning": "oversold", "verdict": "kept"}]}
    result = main._alert_router(state)
    captured = capsys.readouterr().out
    assert "[stdout-alert]" in captured
    assert "AAPL" in captured
    assert result["routed"][0]["sent_to"] == ["stdout"]


def test_router_posts_to_slack_when_configured(patched, monkeypatch):
    calls = []

    def fake_post(url, json=None, timeout=None):
        calls.append((url, json))
        r = mock.MagicMock()
        r.raise_for_status = mock.MagicMock()
        return r

    monkeypatch.setattr(main.requests, "post", fake_post)
    monkeypatch.setenv("SLACK_WEBHOOK_URL", "https://hooks.slack.com/services/XYZ")
    monkeypatch.setattr(main, "DRY_RUN", False)
    state = {"alerts": [{"ticker": "AAPL", "rule_fired": "r",
                         "severity": "med", "reasoning": "x", "verdict": "v"}]}
    result = main._alert_router(state)
    assert any("hooks.slack.com" in u for u, _ in calls)
    assert "slack" in result["routed"][0]["sent_to"]


def test_router_dry_run_forces_stdout_even_with_webhook(patched, monkeypatch, capsys):
    monkeypatch.setenv("SLACK_WEBHOOK_URL", "https://hooks.slack.com/services/XYZ")
    monkeypatch.setattr(main, "DRY_RUN", True)
    state = {"alerts": [{"ticker": "AAPL", "rule_fired": "r",
                         "severity": "med", "reasoning": "x", "verdict": "v"}]}
    result = main._alert_router(state)
    assert "[stdout-alert]" in capsys.readouterr().out
    assert result["routed"][0]["sent_to"] == ["stdout"]


# ── Full graph e2e ────────────────────────────────────────────────────

def test_full_graph_end_to_end(patched, capsys):
    result = main.build_graph().invoke({})
    # Watchlist loaded, candidates emitted (AAPL only), skeptic kept it, router printed.
    assert set(result["watchlist"]) == {"AAPL", "NVDA"}
    assert len(result["candidates"]) == 1
    assert len(result["alerts"]) == 1
    assert len(result["routed"]) == 1
    assert "[stdout-alert]" in capsys.readouterr().out


# ── Safety rail ───────────────────────────────────────────────────────

def test_no_execution_symbols_in_main():
    """Build breaks if anyone adds execution semantics to main.py."""
    src = (Path(__file__).parent / "main.py").read_text().lower()
    forbidden = [
        "place_order", "submit_order", "cancel_order",
        "buy_stock", "sell_stock", "execute_trade", "broker.",
        "alpaca", "ib_insync", "interactive_brokers",
    ]
    for token in forbidden:
        assert token not in src, f"forbidden execution symbol `{token}` found in main.py"


def test_no_execution_symbols_in_requirements():
    reqs = (Path(__file__).parent / "requirements.txt").read_text().lower()
    for broker_dep in ("alpaca", "ib-insync", "ib_insync", "interactive-brokers", "ccxt"):
        assert broker_dep not in reqs, f"broker dep `{broker_dep}` found in requirements"


if __name__ == "__main__":
    sys.exit(pytest.main([__file__, "-v"]))
