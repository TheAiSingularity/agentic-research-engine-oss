"""trading-copilot/production — adaptive verification on top of beginner.

Extends beginner with four additions, each env-gated for ablation:

  T4.1  step critic after gather + after analyze  (ThinkPRM-style)
  T2    self-consistency skeptic (N votes, adaptive sample count)
  T2    CoVe-style _verify_alerts — decomposes each alert's reasoning into
        atomic claims and checks each against the raw prices + news
  +     optional social sources (PRAW, StockTwits) gated by ENABLE_SOCIAL

Skipped (don't transfer to structured-data monitoring):
  HyDE · FLARE · evidence compression · plan refinement · classifier router.
  See ./techniques.md for the reasoning.

EDUCATIONAL RECIPE. No broker integration; no order placement. Research only.
"""

import importlib.util
import os
import sys
from collections import Counter
from concurrent.futures import ThreadPoolExecutor
from pathlib import Path
from typing import TypedDict

sys.path.insert(0, str(Path(__file__).resolve().parents[5]))

# Reuse the beginner module verbatim for data fetching + node helpers.
_BEGINNER_MAIN = Path(__file__).resolve().parents[1] / "beginner/main.py"
_spec = importlib.util.spec_from_file_location("tc_beginner", _BEGINNER_MAIN)
beginner = importlib.util.module_from_spec(_spec)
_spec.loader.exec_module(beginner)

from langgraph.graph import END, StateGraph  # noqa: E402

ENV = os.environ.get
MODEL_PLANNER = ENV("MODEL_PLANNER", "gpt-5-nano")
MODEL_SYNTHESIZER = ENV("MODEL_SYNTHESIZER", "gpt-5-mini")
MODEL_VERIFIER = ENV("MODEL_VERIFIER", MODEL_PLANNER)
MODEL_CRITIC = ENV("MODEL_CRITIC", MODEL_PLANNER)

ENABLE_STEP_VERIFY = ENV("ENABLE_STEP_VERIFY", "1") == "1"
ENABLE_VERIFY = ENV("ENABLE_VERIFY", "1") == "1"
ENABLE_CONSISTENCY = ENV("ENABLE_CONSISTENCY", "1") == "1"
CONSISTENCY_SAMPLES = int(ENV("CONSISTENCY_SAMPLES", "3"))
ENABLE_SOCIAL = ENV("ENABLE_SOCIAL", "0") == "1"
SOCIAL_SUBREDDITS = [s.strip() for s in ENV("SOCIAL_SUBREDDITS", "wallstreetbets,stocks").split(",") if s.strip()]

DISCLAIMER = beginner.DISCLAIMER


class State(TypedDict, total=False):
    watchlist: list[str]
    rules: list[dict]
    prices: dict[str, dict]
    news: dict[str, list[dict]]
    social: dict[str, list[dict]]
    candidates: list[dict]
    alerts: list[dict]            # skeptic-approved
    verified_alerts: list[dict]   # CoVe-checked
    routed: list[dict]
    critic_notes: list[str]       # step-critic feedback for observability


# ── Step critic (T4.1) ────────────────────────────────────────────────

def _critic(step: str, payload: str, context: str) -> tuple[bool, str]:
    if not ENABLE_STEP_VERIFY:
        return True, ""
    prompt = (
        f"You are a step-level verifier for a trading-research pipeline. Reply on two lines:\n"
        f"  VERDICT: accept | redo\n"
        f"  FEEDBACK: <one sentence if redo>\n\n"
        f"Step: {step}\nContext: {context}\nOutput:\n{payload}"
    )
    raw = beginner._chat(MODEL_CRITIC, prompt)
    verdict_line = next((l for l in raw.splitlines() if l.strip().upper().startswith("VERDICT:")), "")
    feedback = next((l.split(":", 1)[1].strip() for l in raw.splitlines()
                     if l.strip().upper().startswith("FEEDBACK:")), "")
    accept = "accept" in verdict_line.lower() or "redo" not in verdict_line.lower()
    return accept, feedback


# ── Optional social data source ───────────────────────────────────────

def _fetch_social(ticker: str) -> list[dict]:
    """Pull a few recent mentions from PRAW (if configured). StockTwits fallback not implemented in beginner tier."""
    if not ENABLE_SOCIAL:
        return []
    client_id = ENV("REDDIT_CLIENT_ID")
    client_secret = ENV("REDDIT_CLIENT_SECRET")
    user_agent = ENV("REDDIT_USER_AGENT", "agentic-research-engine-oss/trading-copilot")
    if not client_id or not client_secret:
        return []
    try:
        import praw  # noqa: F401  (lazy import — only when ENABLE_SOCIAL=1 and creds set)
        reddit = praw.Reddit(client_id=client_id, client_secret=client_secret,
                             user_agent=user_agent)
        mentions: list[dict] = []
        for sub in SOCIAL_SUBREDDITS[:3]:
            for p in reddit.subreddit(sub).search(ticker, limit=3, time_filter="week"):
                mentions.append({"source": f"r/{sub}", "title": p.title, "url": p.url,
                                 "score": int(p.score), "num_comments": int(p.num_comments)})
        return mentions
    except Exception:
        return []


def _gather(state: State) -> dict:
    """Beginner gather + optional social layer."""
    base = beginner._gather(state)
    if ENABLE_SOCIAL:
        tickers = state["watchlist"]
        with ThreadPoolExecutor(max_workers=min(len(tickers), 4)) as pool:
            social = dict(zip(tickers, pool.map(_fetch_social, tickers)))
        base["social"] = social
    else:
        base["social"] = {}
    return base


def _gather_critic(state: State) -> dict:
    """T4.1 step critic — does our gathered data cover the watchlist?"""
    if not ENABLE_STEP_VERIFY:
        return {"critic_notes": state.get("critic_notes", [])}
    summary = {t: {"has_prices": "error" not in state["prices"].get(t, {"error": "missing"}),
                   "n_news": len(state["news"].get(t, []))}
               for t in state["watchlist"]}
    _, feedback = _critic("gather", str(summary), f"Watchlist: {state['watchlist']}")
    notes = state.get("critic_notes", []) + ([f"gather: {feedback}"] if feedback else [])
    return {"critic_notes": notes}


def _analyze(state: State) -> dict:
    """Reuse beginner analyze, then critic the candidates."""
    return beginner._analyze(state)


def _analyze_critic(state: State) -> dict:
    if not ENABLE_STEP_VERIFY:
        return {"critic_notes": state.get("critic_notes", [])}
    payload = "\n".join(f"- {c['ticker']} / {c['rule_fired']}: {c['reasoning']}"
                       for c in state.get("candidates", [])) or "(no candidates)"
    _, feedback = _critic("analyze", payload, f"Rules: {state['rules']}")
    notes = state.get("critic_notes", []) + ([f"analyze: {feedback}"] if feedback else [])
    return {"critic_notes": notes}


# ── Self-consistency skeptic (T2) ─────────────────────────────────────

def _skeptic_vote(candidate: dict, state: State, n_samples: int) -> dict | None:
    """Sample N skeptic verdicts, take majority. Returns enriched alert or None."""
    snap = state["prices"].get(candidate["ticker"], {})
    news = state["news"].get(candidate["ticker"], [])
    news_str = "\n".join(f"- {n['title']}" for n in news[:3]) or "(none)"
    prompt = (f"A candidate alert was produced. Decide keep or drop based on whether the reasoning "
              f"is supported by the data.\n\nCandidate: {candidate}\n"
              f"Snapshot: {snap}\n\nNews:\n{news_str}\n\n"
              f"Reply with exactly two lines:\n"
              f"  VERDICT: keep | drop\n  REASON: <one short sentence>")

    verdicts: list[tuple[str, str]] = []
    for _ in range(n_samples):
        raw = beginner._chat(MODEL_SYNTHESIZER, prompt, temperature=0.3 if n_samples > 1 else 0.0)
        v_line = next((l for l in raw.splitlines() if l.strip().upper().startswith("VERDICT:")), "")
        r_line = next((l for l in raw.splitlines() if l.strip().upper().startswith("REASON:")), "")
        verdict = "keep" if "keep" in v_line.lower() else "drop"
        reason = r_line.split(":", 1)[1].strip() if ":" in r_line else ""
        verdicts.append((verdict, reason))
    majority = Counter(v for v, _ in verdicts).most_common(1)[0][0]
    if majority != "keep":
        return None
    pick = next((r for v, r in verdicts if v == "keep"), "")
    return {**candidate, "verdict": pick, "vote_detail": {"n": n_samples, "kept": sum(1 for v, _ in verdicts if v == "keep")}}


def _skeptic(state: State) -> dict:
    cands = state.get("candidates", [])
    if not cands:
        return {"alerts": []}
    n = CONSISTENCY_SAMPLES if ENABLE_CONSISTENCY else 1
    # Adaptive: high-severity + short reasoning = easy → N=1; low-severity / long = borderline → full N.
    def _n_for(c: dict) -> int:
        if not ENABLE_CONSISTENCY:
            return 1
        if c.get("severity") == "high" and len(c.get("reasoning", "")) < 80:
            return 1
        return n
    with ThreadPoolExecutor(max_workers=min(len(cands), 4)) as pool:
        voted = list(pool.map(lambda c: _skeptic_vote(c, state, _n_for(c)), cands))
    return {"alerts": [a for a in voted if a is not None]}


# ── CoVe-style alert verification (T2) ────────────────────────────────

def _verify_alerts(state: State) -> dict:
    """For each skeptic-approved alert, decompose reasoning into claims and check each against raw data."""
    if not ENABLE_VERIFY:
        return {"verified_alerts": state.get("alerts", [])}
    verified: list[dict] = []
    for alert in state.get("alerts", []):
        ticker = alert["ticker"]
        snap = state["prices"].get(ticker, {})
        news_titles = [n["title"] for n in state["news"].get(ticker, [])[:5]]
        prompt = (
            f"Given the raw data below, list each atomic factual claim in the alert reasoning, "
            f"then for each output `CLAIM: <text>` and on the next line `SUPPORTED: yes | no`.\n\n"
            f"Ticker: {ticker}\nSnapshot: {snap}\nNews: {news_titles}\n\n"
            f"Alert reasoning: {alert.get('reasoning', '')}"
        )
        raw = beginner._chat(MODEL_VERIFIER, prompt)
        claims: list[dict] = []
        current: dict | None = None
        for line in raw.splitlines():
            s = line.strip()
            if s.upper().startswith("CLAIM:"):
                current = {"text": s.split(":", 1)[1].strip(), "supported": False}
                claims.append(current)
            elif s.upper().startswith("SUPPORTED:") and current is not None:
                current["supported"] = "yes" in s.lower()
                current = None
        unsupported = [c["text"] for c in claims if not c["supported"]]
        if unsupported and claims:
            # Drop alert if any claim isn't supported.
            continue
        verified.append({**alert, "verified_claims": claims, "n_claims": len(claims)})
    return {"verified_alerts": verified}


def _alert_router(state: State) -> dict:
    """Route the verified alerts through the beginner router."""
    alerts = state.get("verified_alerts", state.get("alerts", []))
    return beginner._alert_router({**state, "alerts": alerts})


# ── Graph ─────────────────────────────────────────────────────────────

def build_graph():
    g = StateGraph(State)
    nodes = [("load_config", beginner._load_config), ("gather", _gather),
             ("gather_critic", _gather_critic), ("analyze", _analyze),
             ("analyze_critic", _analyze_critic), ("skeptic", _skeptic),
             ("verify_alerts", _verify_alerts), ("alert_router", _alert_router)]
    for n, f in nodes:
        g.add_node(n, f)
    g.set_entry_point("load_config")
    edges = [("load_config", "gather"), ("gather", "gather_critic"),
             ("gather_critic", "analyze"), ("analyze", "analyze_critic"),
             ("analyze_critic", "skeptic"), ("skeptic", "verify_alerts"),
             ("verify_alerts", "alert_router"), ("alert_router", END)]
    for a, b in edges:
        g.add_edge(a, b)
    return g.compile()


if __name__ == "__main__":
    print(DISCLAIMER + "\n")
    result = build_graph().invoke({})
    n_cands = len(result.get("candidates", []))
    n_alerts = len(result.get("alerts", []))
    n_verified = len(result.get("verified_alerts", []))
    n_routed = len(result.get("routed", []))
    print(f"\n[done] watchlist={len(result.get('watchlist', []))}  "
          f"candidates={n_cands}  skeptic={n_alerts}  verified={n_verified}  routed={n_routed}")
    for note in result.get("critic_notes", []):
        print(f"  [critic] {note}")
