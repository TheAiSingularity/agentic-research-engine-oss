# trading-copilot

**Levels:** beginner ✅ · production ✅ · rust ⬛ · eval ✅

> **Research + alerts only — NOT auto-execution.** No broker integration.
> No order placement. Public data only. Not financial advice.
> Enforced by a build-time test that fails if any execution symbol
> (`place_order`, `submit_order`, `buy_stock`, `execute_trade`, `alpaca`,
> `ib_insync`, …) appears in the agent code or requirements.

## What it does

Given a watchlist and a rule set, the agent:

1. Loads tickers + rules from `watchlist.example.yaml`
2. Pulls 6 months of daily OHLCV per ticker via `yfinance`, computes SMA50 / SMA200 / RSI-14
3. Fetches ≤5 recent news headlines per ticker via **self-hosted SearXNG**
4. An **analyst LLM** (cheap tier) decides which rules fire as candidates
5. A **skeptic LLM** (stronger tier) re-reads each candidate against the raw data and either keeps or drops it
6. **Production tier** additionally: step critic after gather + analyze, self-consistency vote on the skeptic, CoVe-style claim verification against raw data, optional Reddit sentiment via PRAW
7. Structured alerts route to Slack / Telegram / Discord webhooks (or stdout in dev mode)

## Stack (April 2026)

| Component | Choice | Notes |
|---|---|---|
| Orchestration | **LangGraph** | Same choice as research-assistant |
| Price data | `yfinance` | Free, no key; 15-min in-memory cache |
| Indicators | `ta` (MIT, pure Python) | SMA, RSI, MACD, Bollinger — no C deps |
| News | **SearXNG** `&categories=news` | Self-hosted, zero external API key |
| Social (production, optional) | `praw` (Reddit) | `ENABLE_SOCIAL=1`; free Reddit app creds |
| Analyst LLM | `MODEL_PLANNER` | `gpt-5-nano` / `gemma4:e2b` / `Qwen3.6` |
| Skeptic LLM | `MODEL_SYNTHESIZER` | `gpt-5-mini` / same local / same VM |
| Alerts | pure `requests.post` to webhooks | Slack / Telegram / Discord; stdout fallback |
| Backtest | pandas + yfinance history | No framework — precision + recall only |

## Pipeline

**Beginner (5 nodes):**
```
load_config → gather → analyze → skeptic → alert_router
```

**Production (8 nodes, all Tier 4 additions env-toggleable):**
```
load_config → gather → gather_critic → analyze → analyze_critic → skeptic (self-consistency×N) → verify_alerts (CoVe) → alert_router
```

See each tier's `techniques.md` for the "why" behind every choice with primary-source citations.

## Three ways to run it

### Mac, fully local (free)
```bash
bash scripts/setup-local-mac.sh      # Ollama + SearXNG (already done if you ran research-assistant)
cd recipes/by-use-case/trading-copilot/beginner
make install
export OPENAI_BASE_URL=http://localhost:11434/v1
export OPENAI_API_KEY=ollama
export MODEL_PLANNER=gemma4:e2b
export MODEL_SYNTHESIZER=gemma4:e2b
export SEARXNG_URL=http://localhost:8888
make smoke
```

### GPU VM (self-hosted)
```bash
bash scripts/setup-vm-gpu.sh --engine sglang --spec-dec \
  --model Qwen/Qwen3.6-35B-A3B
cd recipes/by-use-case/trading-copilot/production
make install
export OPENAI_BASE_URL=http://localhost:8000/v1
export OPENAI_API_KEY=vllm
export MODEL_PLANNER=Qwen/Qwen3.6-35B-A3B
export MODEL_SYNTHESIZER=Qwen/Qwen3.6-35B-A3B
export SEARXNG_URL=http://localhost:8888
make smoke
```

### OpenAI API (pay-per-query)
```bash
cd scripts/searxng && docker compose up -d
cd -
export OPENAI_API_KEY=sk-...
cd recipes/by-use-case/trading-copilot/beginner
make install && make smoke
```

## Alerts — where they go

One-line config per channel. If none set → stdout dev mode.

```bash
export SLACK_WEBHOOK_URL=https://hooks.slack.com/services/...
export TELEGRAM_BOT_TOKEN=...
export TELEGRAM_CHAT_ID=...
export DISCORD_WEBHOOK_URL=https://discord.com/api/webhooks/...

# Or force stdout even if a webhook is set:
export DRY_RUN=1
```

## Backtesting

```bash
cd recipes/by-use-case/trading-copilot/eval
make eval
# → scores precision + recall over fixtures/sample_window.yaml
```

**Known limit:** news used in replay is current-as-of-now, not historical.
See [`eval/README.md`](eval/README.md) for full caveats.

## Testing

All mocked — no API keys, no network:
```bash
cd beginner && make test           # 15 tests
cd ../production && make test      # 15 tests
```
Includes forbidden-symbol safety rails that fail the build if anyone
adds execution semantics to the agent.

## Files

```
trading-copilot/
├── README.md                       # you're reading it
├── beginner/
│   ├── main.py                     # 5-node LangGraph + CLI (~245 LOC)
│   ├── watchlist.example.yaml      # default AAPL / NVDA / TSLA × 2 rules
│   ├── techniques.md               # primary-source citations
│   ├── test_main.py                # 15 mocked tests
│   ├── Makefile · requirements.txt
├── production/
│   ├── main.py                     # adds critic + self-consistency + CoVe + optional social
│   ├── techniques.md               # reasoning per added technique
│   ├── test_production_main.py     # 15 mocked tests
│   ├── README.md · runbook.md
│   ├── Makefile · requirements.txt
└── eval/
    ├── backtest.py                 # replay historical window; precision/recall
    ├── README.md                   # metric explanations + caveats
    ├── Makefile
    └── fixtures/
        └── sample_window.yaml      # AAPL/NVDA/TSLA · Jan–Jun 2024 · ≥3% moves in 5 bars
```

## See also
- [`../research-assistant/`](../research-assistant/) — sister recipe; same OpenAI-compatible + SearXNG stack
- [`docs/how-it-works.md`](../../../docs/how-it-works.md) — elevator pitches + SOTA comparison
