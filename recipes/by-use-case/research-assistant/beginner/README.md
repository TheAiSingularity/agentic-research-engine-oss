# research-assistant/beginner

Canonical beginner-tier research assistant. LangGraph wires a 4-node
pipeline that answers research questions with citations. Works with
OpenAI, Ollama (local), or vLLM (local GPU) — one env var switches
backends.

## What it does

Give it a research question — it plans sub-queries, searches the web via
self-hosted SearXNG, narrows evidence with `core/rag`, and synthesizes a
cited answer.

```
plan ──▶ search (parallel) ──▶ retrieve ──▶ synthesize
(LLM)    (SearXNG → summarize)   (core/rag)   (LLM)
```

No vendor-specific tool calls. Any OpenAI-compatible endpoint works.

## Backends

### 1. Fully local (Mac, Apple Silicon) — **$0 per query**

```bash
bash scripts/setup-local-mac.sh   # installs Ollama + pulls gemma4:e2b + starts SearXNG in Docker

cd recipes/by-use-case/research-assistant/beginner
make install

export OPENAI_BASE_URL=http://localhost:11434/v1
export OPENAI_API_KEY=ollama          # Ollama ignores the key, but SDK requires one
export MODEL_PLANNER=gemma4:e2b
export MODEL_SEARCHER=gemma4:e2b
export MODEL_SYNTHESIZER=gemma4:e2b
export EMBED_MODEL=nomic-embed-text   # local embeddings for core/rag v1 hybrid
export SEARXNG_URL=http://localhost:8888

make smoke
```

### 2. GPU VM (Linux, 4× RTX 6000 Pro Blackwell) — **$0 per query**

```bash
bash scripts/setup-vm-gpu.sh --model Qwen/Qwen3.6-35B-A3B
# installs vLLM, pulls the model, spins up SearXNG

cd recipes/by-use-case/research-assistant/beginner
make install

export OPENAI_BASE_URL=http://localhost:8000/v1
export OPENAI_API_KEY=vllm
export MODEL_PLANNER=Qwen/Qwen3.6-35B-A3B
export MODEL_SEARCHER=Qwen/Qwen3.6-35B-A3B
export MODEL_SYNTHESIZER=Qwen/Qwen3.6-35B-A3B
export EMBED_MODEL=BAAI/bge-m3        # serve a separate embedding model alongside
export SEARXNG_URL=http://localhost:8888

make smoke
```

### 3. OpenAI API (cloud) — pay per query

```bash
cd scripts/searxng && docker compose up -d   # SearXNG still powers search
cd -

cd recipes/by-use-case/research-assistant/beginner
make install

export OPENAI_API_KEY=sk-...
# OPENAI_BASE_URL unset → defaults to https://api.openai.com/v1
# Model names left at defaults: gpt-5-nano (plan), gpt-5-mini (search+synth)
export SEARXNG_URL=http://localhost:8888

make smoke
```

## Stack

| Step | Tool | Why |
|---|---|---|
| plan | `MODEL_PLANNER` (default `gpt-5-nano`) | Cheapest / fastest tier — sub-query generation |
| search | SearXNG + `MODEL_SEARCHER` | Self-hosted meta-search over DuckDuckGo / Bing / Wikipedia / arXiv → LLM summarizes with inline citations |
| retrieve | `core/rag` v0 (OpenAI-compatible embeddings + cosine) | Narrows many highlights to top-k most relevant |
| synthesize | `MODEL_SYNTHESIZER` | Strong reasoning where it matters most — the final cited answer |

See [`techniques.md`](techniques.md) for the SOTA justification on every
choice, with primary-source citations.

## Test (no API key, no network, no model needed)

```bash
make test
```

All external calls are mocked — verifies graph wiring, node contracts,
parallel fan-out, SearXNG parsing, and state shape. 13 tests.

## Override everything

| Env var | Default | Notes |
|---|---|---|
| `OPENAI_BASE_URL` | OpenAI's API | Point at Ollama (`:11434/v1`) or vLLM (`:8000/v1`) |
| `OPENAI_API_KEY` | — | Required by SDK even for local; any value works locally |
| `MODEL_PLANNER` | `gpt-5-nano` | Small, fast model |
| `MODEL_SEARCHER` | `gpt-5-mini` | Summarizes search results |
| `MODEL_SYNTHESIZER` | `gpt-5-mini` | Produces final cited answer |
| `EMBED_MODEL` | `text-embedding-3-small` | Dense embeddings for `core/rag` v1. Local: `nomic-embed-text` (Ollama) or `BAAI/bge-m3` (vLLM) |
| `SEARXNG_URL` | `http://localhost:8888` | Your SearXNG instance |
| `NUM_SUBQUERIES` | `3` | Search fan-out breadth |
| `NUM_RESULTS_PER_QUERY` | `5` | SearXNG results per sub-query |
| `TOP_K_EVIDENCE` | `8` | Evidence chunks kept for synthesis |

## Files

```
beginner/
├── main.py            # The LangGraph agent (100 lines, commented)
├── requirements.txt
├── Makefile           # run · smoke · test · install · clean
├── README.md          # you're reading it
├── techniques.md      # primary-source citations for every choice
└── test_main.py       # mocked unit tests (13, all green)
```
