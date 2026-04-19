# trading-copilot/eval — backtest harness

Offline scoring for the trading-copilot recipe. **Does not place any
orders.** Replays a historical window, runs the pipeline once per scan
date, and compares the alerts it would have fired against the actual
price moves in the following bars.

## Metrics

- **precision** — of the alerts issued, how many were followed by a real
  ≥`threshold_pct` absolute move within `lookahead_days` trading days?
- **recall** — of the meaningful moves in the window, how many were
  flagged by at least one alert?
- **latency_mean_s** — average wall-clock time per scan date.
- **tokens_est_mean** — rough token footprint per scan date.

## Config format (`fixtures/sample_window.yaml`)

```yaml
window:
  start: "2024-01-02"
  end: "2024-06-28"
  every_n_days: 5           # scan every N calendar days

watchlist:
  - AAPL
  - NVDA
  - TSLA

rules:
  - kind: sma_cross
    fast: 50
    slow: 200
  - kind: rsi_oversold
    threshold: 30

scoring:
  threshold_pct: 3.0        # ≥3% absolute move = "meaningful"
  lookahead_days: 5         # within 5 bars of alert's as-of date
```

## Running

```bash
cd recipes/by-use-case/trading-copilot/beginner && make install
cd ../eval
export OPENAI_BASE_URL=http://localhost:11434/v1
export OPENAI_API_KEY=ollama
export MODEL_PLANNER=gemma4:e2b
export MODEL_SYNTHESIZER=gemma4:e2b
export SEARXNG_URL=http://localhost:8888

make eval
```

## Limits & caveats

- **Backtest is only as good as the ground truth we construct.** A "real
  meaningful move" here is purely a `|close[d + lookahead] / close[d] - 1|
  >= threshold_pct` proxy — not a test of whether the alert was a *good
  trade*. Picking better thresholds / asymmetric windows is a future
  improvement.
- **Per-day snapshots use `end_of_day` data.** yfinance returns daily
  bars; intraday signal quality isn't measured.
- **News coverage is "as-of-now," not historical.** SearXNG returns
  current news headlines, not what was on the tape on the replay date.
  This is a known limitation of zero-budget eval — fixing it would
  require a historical news archive (Reuters archive, NewsAPI paid
  historical, etc.). Keep this in mind when interpreting precision.
