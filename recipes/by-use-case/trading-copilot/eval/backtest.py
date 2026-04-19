"""Historical backtest harness for trading-copilot.

Replays a `fixtures/sample_window.yaml` backtest config: for each trading
day in the window, runs the recipe's analyze-skeptic loop against that
day's snapshot, collects all alerts, and scores them against the NEXT
N bars for a real ≥X% move (in the alert's expected direction).

Metrics (identical shape to research-assistant/eval):
  precision — alerts that matched a meaningful move / total alerts
  recall    — meaningful moves flagged / meaningful moves in window
  latency_mean_s / tokens_est_mean per day

Usage:
    python backtest.py                            # uses fixtures/sample_window.yaml
    python backtest.py fixtures/other_window.yaml

NOTE: this module does NOT place any orders. It only measures whether the
recipe's alerts preceded real market moves — pure offline evaluation.
"""

from __future__ import annotations

import importlib.util
import json
import os
import sys
import time
from pathlib import Path
from statistics import mean

import pandas as pd
import yaml
import yfinance as yf

HERE = Path(__file__).resolve().parent
REPO_ROOT = HERE.parents[3]
sys.path.insert(0, str(REPO_ROOT))

BEGINNER_MAIN = REPO_ROOT / "recipes/by-use-case/trading-copilot/beginner/main.py"
_spec = importlib.util.spec_from_file_location("trading_main_bt", BEGINNER_MAIN)
main = importlib.util.module_from_spec(_spec)
os.environ.setdefault("OPENAI_API_KEY", "ollama")
_spec.loader.exec_module(main)


def _load_config(path: Path) -> dict:
    with open(path) as f:
        return yaml.safe_load(f)


def _ground_truth_moves(tickers: list[str], start: str, end: str,
                        threshold_pct: float, lookahead_days: int) -> dict[str, list[pd.Timestamp]]:
    """For each ticker, the list of trading days where close[d+lookahead] / close[d] - 1 >= threshold."""
    moves: dict[str, list[pd.Timestamp]] = {}
    for t in tickers:
        hist = yf.Ticker(t).history(start=start, end=end, auto_adjust=False)
        if hist is None or hist.empty:
            moves[t] = []
            continue
        future = hist["Close"].shift(-lookahead_days)
        ret = (future / hist["Close"] - 1.0) * 100
        dates = hist.index[ret.abs() >= threshold_pct]
        moves[t] = list(dates)
    return moves


def _run_one_day(watchlist: list[str], rules: list[dict]) -> tuple[list[dict], float]:
    """Invoke the pipeline once with the given watchlist+rules; return (alerts, latency_s)."""
    t0 = time.time()
    # Set dry-run so the router doesn't hit any real webhooks during replay.
    os.environ["DRY_RUN"] = "1"
    result = main.build_graph().invoke({"watchlist": watchlist, "rules": rules})
    dt = time.time() - t0
    return result.get("alerts", []), dt


def score_backtest(cfg: dict) -> dict:
    """Replay the window, score precision/recall over alerts.

    Config schema (see fixtures/sample_window.yaml):
      window:       {start: "2024-01-01", end: "2024-06-30", every_n_days: 5}
      watchlist:    [AAPL, NVDA, ...]
      rules:        [{kind: ..., ...}, ...]
      scoring:      {threshold_pct: 3.0, lookahead_days: 5}
    """
    watchlist = cfg["watchlist"]
    rules = cfg["rules"]
    w = cfg["window"]
    s = cfg.get("scoring", {"threshold_pct": 3.0, "lookahead_days": 5})

    truth = _ground_truth_moves(watchlist, w["start"], w["end"],
                                s["threshold_pct"], s["lookahead_days"])
    total_truth_events = sum(len(v) for v in truth.values())

    all_alerts: list[dict] = []
    latencies: list[float] = []
    tokens: list[int] = []

    # Replay — one pipeline invocation per scan date.
    dates = pd.date_range(w["start"], w["end"], freq=f"{w.get('every_n_days', 5)}D")
    print(f"Replaying {len(dates)} scan dates over {len(watchlist)} tickers …")
    for i, d in enumerate(dates, 1):
        alerts, latency = _run_one_day(watchlist, rules)
        for a in alerts:
            a["as_of"] = str(d.date())
            all_alerts.append(a)
        latencies.append(latency)
        tokens.append(sum(len(a.get("reasoning", "")) // 4 + 50 for a in alerts) or 50)
        print(f"  [{i}/{len(dates)}] {d.date()}  alerts={len(alerts)}  {latency:.1f}s")

    # Score: an alert is "matched" if the ticker had a real ≥threshold move within lookahead_days
    # of the alert's as_of date.
    lookahead = pd.Timedelta(days=s["lookahead_days"])
    matched = 0
    for a in all_alerts:
        as_of = pd.Timestamp(a["as_of"])
        window = [d for d in truth.get(a["ticker"], []) if 0 <= (d - as_of).days <= lookahead.days]
        if window:
            matched += 1

    flagged_truths = sum(
        1 for t, events in truth.items() for e in events
        if any(a["ticker"] == t and 0 <= (e - pd.Timestamp(a["as_of"])).days <= lookahead.days
               for a in all_alerts)
    )

    return {
        "n_alerts": len(all_alerts),
        "n_truth_events": total_truth_events,
        "precision": round(matched / len(all_alerts), 3) if all_alerts else 0.0,
        "recall": round(flagged_truths / total_truth_events, 3) if total_truth_events else 0.0,
        "latency_mean_s": round(mean(latencies), 2) if latencies else 0.0,
        "tokens_est_mean": round(mean(tokens), 0) if tokens else 0,
    }


if __name__ == "__main__":
    cfg_path = Path(sys.argv[1]) if len(sys.argv) > 1 else HERE / "fixtures/sample_window.yaml"
    print(f"Backtest config: {cfg_path}\n")
    scores = score_backtest(_load_config(cfg_path))
    print("\n" + json.dumps(scores, indent=2))
