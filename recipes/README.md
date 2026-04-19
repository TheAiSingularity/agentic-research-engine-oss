# `recipes/`

Runnable agent apps. Two indexes:

- [`by-use-case/`](by-use-case/) — organized by outcome (research / analysis / trading / ...)
- [`by-pattern/`](by-pattern/) — organized by technique (ReAct, RAG, multi-agent crew, MCP server, ...)

## Wave 1 recipes

| Recipe | Persona | Frameworks compared |
|---|---|---|
| [research-assistant/](by-use-case/research-assistant/) | Knowledge worker | vanilla · langgraph · crewai · llamaindex |
| [youtube-analyzer/](by-use-case/youtube-analyzer/) | Creator economy | vanilla · langgraph · crewai · pydantic-ai |
| [trading-copilot/](by-use-case/trading-copilot/) | Investor / quant | vanilla · langgraph · openai-agents-sdk · dspy |

## Recipe levels

Every recipe declares its available levels with a badge in its README:

- **beginner** ✅ — always present. Single-file, ≤100 lines, `make run` in ≤60s.
- **production** ⬛ — opt-in. Real tests, observability, HermesClaw sandbox, SLO/cost numbers.
- **rust** ⬛ — opt-in. Only where Rust genuinely wins.

## Framework comparison

Each recipe ships with a `comparison.md` that holds the benchmark table across all its framework implementations:

| Dimension | vanilla | langgraph | crewai | ... |
|---|---|---|---|---|
| Code clarity (lines) | | | | |
| Tokens per run | | | | |
| Latency p50 / p95 | | | | |
| Cost per run (USD) | | | | |
| Accuracy on eval set | | | | |

These pages are the highest-SEO-leverage content in the repo — "CrewAI vs LangGraph for X" queries rank them.

## Adding a recipe

See the root [CONTRIBUTING.md](../CONTRIBUTING.md). TL;DR: open a **recipe-request** issue first, use the existing structure as template, `make run` must work in ≤60s.
