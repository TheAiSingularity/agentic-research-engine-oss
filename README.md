<p align="center">
  <strong>agentic-ai-cookbook-lab · the engine</strong>
</p>

<p align="center">
  <a href="LICENSE"><img src="https://img.shields.io/badge/license-MIT-blue.svg" alt="License"></a>
  <img src="https://img.shields.io/badge/status-private%20alpha-orange.svg" alt="Status">
  <img src="https://img.shields.io/badge/default-gemma%203%204B%20local-green.svg" alt="Default">
  <img src="https://img.shields.io/badge/tests-215%2F215-brightgreen.svg" alt="Tests">
  <img src="https://img.shields.io/badge/interfaces-CLI%20%7C%20TUI%20%7C%20web-blue.svg" alt="Interfaces">
</p>

**The best $0 research agent that runs on a laptop.** Open-source
end-to-end, reproducible, privacy-preserving. No cloud dependency by
default; no telemetry; every LLM call, every source, and every
verification decision is visible.

Runs fully local on Mac M-series via Ollama + Gemma 3 4B + SearXNG +
trafilatura. Same code runs against any OpenAI-compatible endpoint via
one env var (`OPENAI_BASE_URL`) — so OpenAI / vLLM / SGLang are
`--api-key`-away when you want them.

For the deep technical spec, see [`docs/architecture.md`](docs/architecture.md).
For the wave-by-wave build log, see [`docs/progress.md`](docs/progress.md).
For the master plan, see [`.project/plans/research-engine-master-plan.md`](.project/plans/research-engine-master-plan.md).

---

## What ships

### `engine/` — the flagship research engine

8-node LangGraph pipeline + memory + compaction + three interfaces + MCP
distribution + plugin loader:

- **Pipeline:** `classify → plan → search → retrieve → fetch_url → compress → synthesize → verify` with 2026-SOTA composition — HyDE, CoVe verification, iterative retrieval, FLARE active retrieval, classifier router, step critic, LongLLMLingua-style compression, cross-encoder rerank, contextual chunking. Every stage env-toggleable for ablation.
- **Three interfaces, all in parallel**: `engine.interfaces.cli` (rich stdout), `engine.interfaces.tui` (Textual — works over SSH), `engine.interfaces.web` (FastAPI + HTMX on `localhost:8080`).
- **Memory (opt-in)**: SQLite trajectory log at `~/.agentic-research/memory.db` with semantic retrieval. Three modes: `off` / `session` / `persistent`. Wipe with `engine reset-memory`.
- **Context compaction**: auto-trims evidence above `CONTEXT_LIMIT_CHARS` while preserving load-bearing (CoVe-verified) URLs.
- **Six domain presets**: `general`, `medical`, `papers`, `financial`, `stock_trading`, `personal_docs`. YAML-configured in `engine/domains/`. Add your own in <5 min (see [`docs/domains.md`](docs/domains.md)).
- **MCP server**: Python stdio MCP exposing one `research` tool + `reset_memory` + `memory_count`. Ready to register in Claude Desktop / Cursor / Continue.
- **Claude plugin bundle**: `engine/mcp/claude_plugin/` with four skills (`/research`, `/cite-sources`, `/verify-claim`, `/set-domain`). Submittable to Anthropic's marketplace.
- **Plugin loader**: install third-party Claude plugins or Hermes (`agentskills.io`) skills via `engine plugins install gh:owner/repo` or `file:/path`.

### `core/rag/` — shared retrieval primitives

`HybridRetriever` (BM25 + dense + RRF), `CrossEncoderReranker`
(`BAAI/bge-reranker-v2-m3`), `contextualize_chunks` (Anthropic pattern),
`CorpusIndex` (bring-your-own-PDFs). 5 exports, stable v1, used by the
engine and the archived recipes.

### `archive/recipes/` — historical cookbook recipes

Pre-engine recipes kept as reference implementations. The
research-assistant production pipeline is now a thin shim over
`engine.core.pipeline` (zero behavior drift, all tests still green).

---

## Quickstart (Mac local)

```bash
# Prerequisites
brew install ollama                 # or ollama.com/download
ollama pull gemma3:4b nomic-embed-text
(cd scripts/searxng && docker compose up -d)

# Engine
git clone https://github.com/TheAiSingularity/agentic-ai-cookbook-lab
cd agentic-ai-cookbook-lab/engine
make install
make smoke                          # canonical end-to-end run
```

Expected wall-clock on M4 Pro: **~45 s** for a factoid, ~90 s for
multi-hop synthesis. Zero dollars.

### Three ways to drive it

```bash
# CLI
engine ask "What is Anthropic's contextual retrieval?" --domain papers --memory session

# TUI
make tui                            # Textual interface; keyboard-driven

# Web GUI
make gui                            # FastAPI + HTMX at http://localhost:8080
```

### Cloud fallback (opt-in)

```bash
engine ask "…" --api-key sk-... --model gpt-5-mini
# Same pipeline. Different backend. ~$0.003 / query at gpt-5-mini prices.
```

### Bring your own documents

```bash
python scripts/index_corpus.py build ~/papers --out ~/papers.idx
export LOCAL_CORPUS_PATH=~/papers.idx
engine ask "what does my library say about X?" --domain personal_docs
```

---

## What's new / status

| | |
|---|---|
| Status | Private alpha. Public launch in Phase 9 of the master plan. |
| Default model | `gemma3:4b` (3.3 GB via Ollama) |
| Tests | **215+** mocked, all green, no network or API key needed |
| Interfaces | CLI · TUI · Web GUI (all three shipped) |
| MCP | Python server + submittable Claude plugin bundle |
| Memory | Trajectory log + semantic retrieval (SQLite) |
| Domains | 6 built-in presets, easy to extend |
| Plugin loader | Claude plugins + Hermes skills |
| Honest quality ceiling | 4 B-class; expect 15-25% below 30 B+ on complex multi-hop. See `engine/benchmarks/RESULTS.md`. |

---

## Repo layout

```
agentic-ai-cookbook-lab/
├── engine/                        the flagship research engine (Phase 1+)
│   ├── core/                      pipeline · models · trace · memory · compaction · domains · plugins
│   ├── interfaces/                cli · tui · web
│   ├── mcp/                       Python MCP server + Claude plugin bundle
│   ├── domains/                   6 YAML presets
│   ├── examples/                  5 worked research examples
│   ├── benchmarks/                mini fixtures + RESULTS.md
│   └── tests/                     mocked pytest suite
├── core/rag/                      shared retrieval primitives (stable v1)
├── archive/                       pre-engine recipes (kept for reference)
├── scripts/
│   ├── searxng/                   self-hosted SearXNG (docker-compose)
│   ├── setup-local-mac.sh         Mac + Ollama one-liner
│   ├── setup-vm-gpu.sh            Linux + vLLM/SGLang
│   └── index_corpus.py            build a CorpusIndex from PDFs/md/txt
├── docs/
│   ├── architecture.md            deep technical spec
│   ├── plugins-skills.md          how to write + install plugins
│   ├── domains.md                 how to write a domain preset
│   ├── self-learning.md           trajectory logging + memory model
│   ├── progress.md                wave-by-wave build log
│   ├── how-it-works.md            elevator pitches + SOTA comparison
│   └── paper-draft.md             (future) arXiv tech report
├── CONTRIBUTING.md
├── CODE_OF_CONDUCT.md
├── LICENSE                        MIT
└── README.md                      you're reading it
```

---

## Related (sibling projects)

- [HermesClaw](https://github.com/TheAiSingularity/hermesclaw) — secure runtime these recipes can run inside
- [NVIDIA/OpenShell](https://github.com/NVIDIA/OpenShell) — kernel-level agent sandbox
- [NousResearch/hermes-agent](https://github.com/NousResearch/hermes-agent) — self-improving agent (whose `agentskills.io` skill format we interoperate with)

---

## License

MIT. See [`LICENSE`](LICENSE).

Contributions welcome. Read [`CONTRIBUTING.md`](CONTRIBUTING.md) first;
good-first-issues labeled on GitHub.
