# Techniques — trading-copilot/beginner

Every choice, with primary-source justification. This is a **research and
alerts** recipe: no broker integration, no order execution, public data only.

---

## Framework: LangGraph

**Why:** The same rationale as research-assistant — lowest token overhead
for stateful workflows, graph nodes with direct state transitions. A
5-node pipeline (`load_config → gather → analyze → skeptic → alert_router`)
maps cleanly onto LangGraph's `StateGraph`.

- [2026 AI Agent Framework Decision Guide (dev.to)](https://dev.to/linou518/the-2026-ai-agent-framework-decision-guide-langgraph-vs-crewai-vs-pydantic-ai-b2h)

## Prices: `yfinance`

**Why:** Apache-2.0, no API key, mainstream. The most frictionless way to
pull OHLCV for US equities in 2026.

**Gotcha:** Yahoo Finance scrapes routinely hit rate limits; yfinance has
known periodic outages. Wrap with a 15-minute in-memory cache
(`_price_cache`) so re-runs within the TTL don't re-fetch. For production
deployments at scale, consider `alpaca-py` with its free IEX endpoint or
Polygon's paid tier.

- [yfinance on PyPI](https://pypi.org/project/yfinance/)
- [Why yfinance keeps getting blocked (Medium)](https://medium.com/@trading.dude/why-yfinance-keeps-getting-blocked-and-what-to-use-instead-92d84bb2cc01)

## Technical indicators: `ta`

**Why:** Pure Python, MIT, no C dependency (unlike TA-Lib). 80+
indicators — more than enough for the 4 rule kinds we ship
(SMA, RSI, MACD, Bollinger Bands). `pandas-ta` is the alternative for
150+ indicators if the user needs more.

- [bukosabino/ta — GitHub](https://github.com/bukosabino/ta)

## News: SearXNG (`&categories=news`) — primary; `feedparser` fallback

**Why SearXNG:** We already self-host it for research-assistant; reusing
the same instance across recipes is zero marginal cost. The JSON API
accepts a `categories=news` parameter that returns Google News / Yahoo
News / Bing News / Reuters RSS aggregations — no API key required.

**Why `feedparser` as documented fallback:** If the user doesn't run
SearXNG, `feedparser` on Google News RSS
(`news.google.com/rss/search?q=TICKER`) is a ~5-line alternative with
no authentication. Ships in `requirements.txt` so it's available but
the default code path uses SearXNG.

- [SearXNG JSON API docs](https://docs.searxng.org/user/search_api.html)
- [feedparser on PyPI](https://pypi.org/project/feedparser/)

## Two-role LLM pipeline: cheap analyst → escalated skeptic

**Why split roles:**
- **Analyst** runs on every ticker in the watchlist — potentially many
  calls per scan. Use the cheapest tier (`MODEL_PLANNER` = `gpt-5-nano` /
  `gemma4:e2b` / `Qwen3.6`).
- **Skeptic** runs only on triggered *candidates* — typically a small
  fraction of the watchlist. This is the step where reasoning quality
  matters most (catching false positives). Use the stronger tier
  (`MODEL_SYNTHESIZER` = `gpt-5-mini` / same local / same VM).

**Why it saves money:** On a 50-ticker watchlist where 3 tickers fire
rules, you pay 50 × cheap + 3 × expensive instead of 50 × expensive.
This matches the standard 2026 "model routing" pattern — cheap default,
expensive on the step where it matters.

- [Artificial Analysis model leaderboard](https://artificialanalysis.ai/leaderboards/models)
- [LM Council benchmarks](https://lmcouncil.ai/benchmarks)

## Structured output via `CANDIDATE:` / `VERDICT:` protocol

**Why structured lines (not JSON):** Tiny open-weight models
(`gemma4:e2b`, 2B effective) are unreliable at JSON output but accept
line-prefix protocols like `CANDIDATE: …` / `VERDICT: …` extremely well.
Same pattern used in research-assistant's CoVe verifier. Fail-soft: any
un-parseable line is skipped, not errored.

## Alert routing: pure `requests.post(webhook, json=…)`

**Why not SDKs:** Slack's `slack-sdk`, Telegram's `python-telegram-bot`,
etc. all add transitive dependencies and OAuth scaffolding we don't need.
A webhook URL + a single `requests.post` is 2 lines per channel, works
identically across Slack / Telegram / Discord.

- [Slack incoming webhooks](https://api.slack.com/messaging/webhooks)
- [Telegram `sendMessage` API](https://core.telegram.org/bots/api#sendmessage)
- [Discord webhooks](https://discord.com/developers/docs/resources/webhook)

## Backtesting: pandas-only (no framework)

**Why:** We only need to replay a historical window, fire the pipeline
on each "as-of" date, and compute `precision = (alerts matching real
≥N% moves) / (alerts issued)` and `recall = (meaningful moves flagged)
/ (meaningful moves in window)`. That's 100 lines of pandas.
`vectorbt` / `backtrader` are overkill here.

See [`../eval/backtest.py`](../eval/backtest.py).

## What nobody tells you

**The "LLM analyst + LLM skeptic" pattern quietly inherits the same
adversarial-verification structure as Chain-of-Verification.** Instead
of verifying atomic claims like in research-assistant's CoVe, the
skeptic here verifies composite signals against the raw numeric
snapshot + news headlines. When the LLM analyst hallucinates a trigger
("RSI below 30" when it's actually 55), the skeptic catches it because
the raw data it sees disagrees with the claim. Same verification
principle, different domain.

This is why the **production tier** layering is cheap: we just reuse
`_critic` (ThinkPRM step-level) from research-assistant, plus add a
CoVe-equivalent `_verify_alerts` node. The architectural story stays
consistent across recipes.
