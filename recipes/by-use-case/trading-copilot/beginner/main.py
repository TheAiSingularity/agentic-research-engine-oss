"""trading-copilot/beginner — market research + alerts (NOT auto-execution).

EDUCATIONAL RECIPE. This agent researches a watchlist of tickers, applies
rule-based triggers against live market data + news, runs an LLM skeptic
over candidate signals, and emits structured alerts to Slack / Telegram /
Discord webhooks (or stdout in dev mode). No broker integration; no order
placement; no auto-trading. Not financial advice.

LangGraph pipeline (5 nodes):
  load_config → gather → analyze → skeptic → alert_router → END

Talks to any OpenAI-compatible LLM endpoint via OPENAI_BASE_URL (OpenAI,
Ollama, vLLM, SGLang) and uses self-hosted SearXNG for news — no paid
search API.
"""

import os
import sys
import time
from concurrent.futures import ThreadPoolExecutor
from pathlib import Path
from typing import TypedDict

sys.path.insert(0, str(Path(__file__).resolve().parents[5]))

import requests  # noqa: E402
import yaml  # noqa: E402
import yfinance as yf  # noqa: E402
from langgraph.graph import END, StateGraph  # noqa: E402
from openai import OpenAI  # noqa: E402
from ta.momentum import rsi  # noqa: E402
from ta.trend import sma_indicator  # noqa: E402

ENV = os.environ.get
MODEL_PLANNER = ENV("MODEL_PLANNER", "gpt-5-nano")
MODEL_SYNTHESIZER = ENV("MODEL_SYNTHESIZER", "gpt-5-mini")
SEARXNG_URL = ENV("SEARXNG_URL", "http://localhost:8888")
WATCHLIST_FILE = ENV("WATCHLIST_FILE", str(Path(__file__).parent / "watchlist.example.yaml"))
NUM_NEWS_PER_TICKER = int(ENV("NUM_NEWS_PER_TICKER", "5"))
YFINANCE_CACHE_TTL_SEC = int(ENV("YFINANCE_CACHE_TTL_SEC", "900"))
DRY_RUN = ENV("DRY_RUN", "0") == "1"

DISCLAIMER = ("⚠  trading-copilot — research & alerts ONLY, NOT auto-execution. "
              "Not financial advice. Public data only.")


class State(TypedDict, total=False):
    watchlist: list[str]
    rules: list[dict]
    prices: dict[str, dict]
    news: dict[str, list[dict]]
    candidates: list[dict]
    alerts: list[dict]
    routed: list[dict]


def _llm() -> OpenAI:
    return OpenAI(api_key=ENV("OPENAI_API_KEY", "ollama"), base_url=ENV("OPENAI_BASE_URL"))


def _chat(model: str, prompt: str, temperature: float = 0.0) -> str:
    resp = _llm().chat.completions.create(
        model=model, messages=[{"role": "user", "content": prompt}], temperature=temperature
    )
    return resp.choices[0].message.content or ""


_price_cache: dict[str, tuple[float, dict]] = {}


def _fetch_prices(ticker: str) -> dict:
    """Pull 6mo daily OHLCV from yfinance, compute compact snapshot + indicators. Cached."""
    now, cached = time.time(), _price_cache.get(ticker)
    if cached and now - cached[0] < YFINANCE_CACHE_TTL_SEC:
        return cached[1]
    hist = yf.Ticker(ticker).history(period="6mo", interval="1d", auto_adjust=False)
    if hist is None or hist.empty:
        snap = {"ticker": ticker, "error": "no data"}
    else:
        close = hist["Close"]
        snap = {
            "ticker": ticker, "last": round(float(close.iloc[-1]), 4),
            "pct_change_1d": round(float(close.pct_change().iloc[-1] * 100), 3),
            "sma50": round(float(sma_indicator(close, window=50).iloc[-1]), 4),
            "sma200": round(float(sma_indicator(close, window=200).iloc[-1]), 4),
            "rsi14": round(float(rsi(close, window=14).iloc[-1]), 2),
            "closes_tail": [round(float(x), 4) for x in close.tail(5).tolist()],
        }
    _price_cache[ticker] = (now, snap)
    return snap


def _fetch_news(ticker: str) -> list[dict]:
    """Top-N news headlines for a ticker via SearXNG's news category."""
    try:
        r = requests.get(f"{SEARXNG_URL}/search",
                         params={"q": f"{ticker} stock", "categories": "news", "format": "json"},
                         timeout=20)
        r.raise_for_status()
    except Exception:
        return []
    return [{"url": h.get("url", ""), "title": h.get("title", ""),
             "snippet": h.get("content", ""), "published": h.get("publishedDate", "")}
            for h in (r.json().get("results") or [])[:NUM_NEWS_PER_TICKER]]


# ── Nodes ──────────────────────────────────────────────────────────

def _load_config(state: State) -> dict:
    """Load watchlist + rules from YAML (if not already supplied in state)."""
    if state.get("watchlist") and state.get("rules"):
        return {}
    cfg = yaml.safe_load(Path(WATCHLIST_FILE).read_text())
    watchlist = [t.upper().strip() for t in cfg.get("watchlist", []) if t.strip().isalnum()]
    rules = cfg.get("rules", [])
    return {"watchlist": watchlist, "rules": rules}


def _gather(state: State) -> dict:
    """Parallel fetch: prices (yfinance) + news (SearXNG) per ticker."""
    tickers = state["watchlist"]
    with ThreadPoolExecutor(max_workers=min(len(tickers) * 2, 8)) as pool:
        prices = dict(zip(tickers, pool.map(_fetch_prices, tickers)))
        news = dict(zip(tickers, pool.map(_fetch_news, tickers)))
    return {"prices": prices, "news": news}


def _analyze(state: State) -> dict:
    """Per-ticker LLM pass: match rules against snapshot + news, emit candidate signals."""
    rules_str = "\n".join(f"- {r}" for r in state["rules"])
    candidates: list[dict] = []
    for ticker in state["watchlist"]:
        snap = state["prices"].get(ticker, {})
        if "error" in snap:
            continue
        news = state["news"].get(ticker, [])
        news_str = "\n".join(f"- {n['title']}" for n in news[:5]) or "(no news)"
        prompt = (f"You are a market analyst. For ticker {ticker}, decide which rules fire.\n\n"
                  f"Snapshot: {snap}\n\nNews headlines:\n{news_str}\n\nRules:\n{rules_str}\n\n"
                  f"For each rule that fires, output exactly one line:\n"
                  f"  CANDIDATE: <rule_kind> | severity=<low|med|high> | <one-sentence reason>\n"
                  f"If no rule fires, output nothing.")
        for line in _chat(MODEL_PLANNER, prompt).splitlines():
            if not line.strip().startswith("CANDIDATE:"):
                continue
            body = line.split(":", 1)[1]
            parts = [p.strip() for p in body.split("|")]
            if len(parts) < 3:
                continue
            rule_kind, sev_kv, reason = parts[0], parts[1], "|".join(parts[2:])
            severity = sev_kv.split("=")[-1].strip() if "=" in sev_kv else "med"
            candidates.append({"ticker": ticker, "rule_fired": rule_kind,
                               "severity": severity, "reasoning": reason.strip()})
    return {"candidates": candidates}


def _skeptic(state: State) -> dict:
    """One LLM call per candidate (parallel); filter false positives; stronger model."""
    cands = state.get("candidates", [])
    if not cands:
        return {"alerts": []}

    def _judge(c: dict) -> dict | None:
        snap = state["prices"].get(c["ticker"], {})
        news = state["news"].get(c["ticker"], [])
        news_str = "\n".join(f"- {n['title']}" for n in news[:3]) or "(none)"
        prompt = (f"A candidate alert was produced. Decide whether to keep or drop it based on whether "
                  f"the reasoning is supported by the data.\n\nCandidate: {c}\n"
                  f"Snapshot: {snap}\n\nNews:\n{news_str}\n\n"
                  f"Reply with exactly two lines:\n"
                  f"  VERDICT: keep | drop\n  REASON: <one short sentence>")
        out = _chat(MODEL_SYNTHESIZER, prompt)
        verdict_line = next((l for l in out.splitlines() if l.strip().upper().startswith("VERDICT:")), "")
        reason_line = next((l for l in out.splitlines() if l.strip().upper().startswith("REASON:")), "")
        if "keep" not in verdict_line.lower():
            return None
        return {**c, "verdict": reason_line.split(":", 1)[1].strip() if ":" in reason_line else ""}

    with ThreadPoolExecutor(max_workers=min(len(cands), 4)) as pool:
        alerts = [a for a in pool.map(_judge, cands) if a is not None]
    return {"alerts": alerts}


def _format_alert_message(alert: dict) -> str:
    return (f"*{alert['ticker']}* — {alert['rule_fired']} (severity: {alert['severity']})\n"
            f"_Analyst:_ {alert['reasoning']}\n_Skeptic:_ {alert.get('verdict', '')}")


def _alert_router(state: State) -> dict:
    """POST alerts to any configured webhook (Slack/Telegram/Discord); else stdout."""
    alerts = state.get("alerts", [])
    routed: list[dict] = []
    slack = ENV("SLACK_WEBHOOK_URL")
    telegram_token, telegram_chat = ENV("TELEGRAM_BOT_TOKEN"), ENV("TELEGRAM_CHAT_ID")
    discord = ENV("DISCORD_WEBHOOK_URL")
    for alert in alerts:
        msg = _format_alert_message(alert)
        sent_to: list[str] = []
        if not DRY_RUN:
            if slack:
                try:
                    requests.post(slack, json={"text": msg}, timeout=10).raise_for_status()
                    sent_to.append("slack")
                except Exception:  # pragma: no cover
                    pass
            if telegram_token and telegram_chat:
                try:
                    requests.post(f"https://api.telegram.org/bot{telegram_token}/sendMessage",
                                  json={"chat_id": telegram_chat, "text": msg, "parse_mode": "Markdown"},
                                  timeout=10).raise_for_status()
                    sent_to.append("telegram")
                except Exception:  # pragma: no cover
                    pass
            if discord:
                try:
                    requests.post(discord, json={"content": msg}, timeout=10).raise_for_status()
                    sent_to.append("discord")
                except Exception:  # pragma: no cover
                    pass
        if not sent_to:
            print(f"[stdout-alert] {msg}\n")
            sent_to.append("stdout")
        routed.append({**alert, "sent_to": sent_to})
    return {"routed": routed}


def build_graph():
    g = StateGraph(State)
    for n, f in [("load_config", _load_config), ("gather", _gather), ("analyze", _analyze),
                 ("skeptic", _skeptic), ("alert_router", _alert_router)]:
        g.add_node(n, f)
    g.set_entry_point("load_config")
    for a, b in [("load_config", "gather"), ("gather", "analyze"), ("analyze", "skeptic"),
                 ("skeptic", "alert_router"), ("alert_router", END)]:
        g.add_edge(a, b)
    return g.compile()


if __name__ == "__main__":
    print(DISCLAIMER + "\n")
    result = build_graph().invoke({})
    n_alerts = len(result.get("routed", []))
    print(f"\n[done] {len(result.get('watchlist', []))} tickers scanned, "
          f"{len(result.get('candidates', []))} candidates, "
          f"{len(result.get('alerts', []))} passed skeptic, {n_alerts} routed")
