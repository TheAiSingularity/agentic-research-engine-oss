# `recipes/`

Opinionated SOTA agent recipes. One implementation per task — best
framework, retrieval stack, LLM routing, eval — for *that* task.

Two indexes:
- [`by-use-case/`](by-use-case/) — organized by outcome
- [`by-pattern/`](by-pattern/) — organized by technique (currently: Rust MCP case study)

## Live recipes

| Recipe | Status | What it does |
|---|---|---|
| [research-assistant/](by-use-case/research-assistant/) | **beginner + production shipped**, eval harness + 12-config ablation matrix | Deep-research agent: decompose → search → fetch → retrieve → compress → synthesize → verify → iterate. Tier 2 + Tier 4 + Wave 4–7 techniques, all env-toggleable. |
| [trading-copilot/](by-use-case/trading-copilot/) | **beginner + production shipped**, backtest harness | Market research + alerts on a watchlist + rule set. Cheap analyst + escalated skeptic + CoVe-style claim verification against raw data. Slack/Telegram/Discord webhooks or stdout. Build-time safety test forbids any execution symbol. |
| [document-qa/](by-use-case/document-qa/) | **beginner shipped** | Bring-your-own-documents Q&A. 4-node pipeline over a `CorpusIndex` built from PDFs / markdown / text / HTML. Hybrid retrieval + streaming synthesis + CoVe verify. No web reach — build-time test forbids `searxng`, `requests.get`, `trafilatura.fetch_url`. |
| [by-pattern/rust-mcp-search-tool/](by-pattern/rust-mcp-search-tool/) | Cargo scaffolded, Dockerfile included | Rust MCP server wrapping SearXNG — ~5 MB binary, 4 ms cold start. Case study in where Rust genuinely wins. |

## Portable stack — every recipe talks to any OpenAI-compatible endpoint

| Step | Default model (OpenAI) | Mac-local (Ollama) | GPU VM (vLLM / SGLang) |
|---|---|---|---|
| planner / classifier / critic / compressor | `gpt-5-nano` | `gemma4:e2b` | `Qwen/Qwen3.6-35B-A3B` |
| searcher / synthesizer / verifier | `gpt-5-mini` | `gemma4:e2b` | `Qwen/Qwen3.6-35B-A3B` |
| embeddings | `text-embedding-3-small` | `nomic-embed-text` | `BAAI/bge-m3` |
| web search | — (replaced by SearXNG below) | | |
| search provider | **SearXNG** (self-hosted, meta-searches DDG/Bing/Wikipedia/arXiv) | same | same |

Point `OPENAI_BASE_URL` at `:11434/v1` (Ollama) or `:8000/v1` (vLLM/SGLang)
or leave unset (OpenAI default). `EMBED_MODEL` controls the embedding
tag. That's the whole config surface.

## Recipe levels

- **`beginner/`** — lean reference implementation. ≤100 LOC, single file,
  heavy comments. `make run` in ≤60–90 s.
- **`production/`** — full adaptive-verification stack. All Tier 2 + Tier 4
  techniques, every one independently env-gated.
- **`rust/`** (optional) — where Rust genuinely wins.

## Adding a recipe

See root [CONTRIBUTING.md](../CONTRIBUTING.md). TL;DR:
- Open a **recipe-request** issue first with the proposed SOTA stack + rationale
- Use `research-assistant/` as the template structure
- `make run` in ≤90 s from a fresh clone
- Ship `techniques.md` (primary-source citations) + `eval/` (reproducible scorer)
