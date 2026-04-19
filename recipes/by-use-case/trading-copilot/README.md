# trading-copilot

**Levels:** beginner ⬛ · production ⬛ · rust ⬛ · **all pending — ships in Wave 1**

> **This is a research and alerting tool — NOT an auto-execution bot.** No orders are placed. No broker integration. Educational use only.

## What it does
Given a watchlist and a research question, fetches market data (public APIs — Yahoo Finance via `yfinance`), pulls news/sentiment, applies LLM reasoning, and emits structured alerts to Slack or Telegram when pre-defined conditions are met.

## Who it's for
- Retail investors / quants building research tooling
- Anyone learning how to do streaming-data agents, stateful monitoring, and routed alerts
- Developers comparing how each framework handles long-running / always-on agent patterns

## Why you'd use it
- Covers a genuinely different pattern than research-assistant and youtube-analyzer — this one is **stateful and continuous**
- Public data sources only — no broker API, no real money, no regulatory headaches
- Alerts are routed, not placed — the human stays in the loop

## Framework implementations (Wave 1)

| Variant | Why this framework |
|---|---|
| [`beginner/vanilla/`](beginner/vanilla/) | Baseline — cron + tool-calling loop |
| [`beginner/langgraph/`](beginner/langgraph/) | Stateful graph — best fit for long-running monitoring |
| [`beginner/openai-agents-sdk/`](beginner/openai-agents-sdk/) | Lightweight tool-calling — the former OpenAI Swarm evolved into Agents SDK |
| [`beginner/dspy/`](beginner/dspy/) | Declarative reasoning — shows how to optimize the prompt chain over time |

## See also
- [`comparison.md`](comparison.md) — benchmark table across the four implementations (lands Wave 1)
