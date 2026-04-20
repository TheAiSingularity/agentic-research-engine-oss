<p align="center">
  <strong>agentic-ai-cookbook-lab</strong>
</p>

<p align="center">
  <a href="LICENSE"><img src="https://img.shields.io/badge/license-MIT-blue.svg" alt="License"></a>
  <img src="https://img.shields.io/badge/status-wave%205-brightgreen.svg" alt="Status">
  <img src="https://img.shields.io/badge/recipes-2%20flagship%20%2B%201%20rust-green.svg" alt="Recipes">
  <img src="https://img.shields.io/badge/tests-135%2F135-brightgreen.svg" alt="Tests">
  <img src="https://img.shields.io/badge/languages-python%20%2B%20rust-green.svg" alt="Languages">
</p>

**SOTA research agents that verify their own answers, runnable on any LLM backend, $0 per query when self-hosted.**

The OpenAI / Anthropic Cookbook model, applied to agentic research:
one opinionated, benchmarked implementation per task. No vendor lock-in —
everything talks to any OpenAI-compatible endpoint via one env var
(`OPENAI_BASE_URL`), so the same code runs on OpenAI, **Ollama** (Mac),
**vLLM** or **SGLang** (Linux GPU). Search is **self-hosted SearXNG** —
no paid search API. Full-page content via **trafilatura**. Reranking via
**BAAI/bge-reranker-v2-m3**. All Apache-2.0 / MIT.

For a fuller explanation at three depths (30-second / 2-minute /
technical) and an honest comparison vs GPT-5.4 Pro, MiroThinker-H1, and
OpenResearcher-30B-A3B, see [`docs/how-it-works.md`](docs/how-it-works.md).
For the wave-by-wave build log see [`docs/progress.md`](docs/progress.md).

---

## Recipes

| Recipe | Levels | What it does |
|---|---|---|
| [**research-assistant**](recipes/by-use-case/research-assistant/) | `beginner` (100 LOC) · `production` (~485 LOC; Tier 2 + Tier 4 + Wave 4 + Wave 5) · `eval` harness w/ 12-config ablation | Answers hard research questions with cited sources; decomposes → searches → fetches → reranks → compresses → verifies → iterates |
| [**trading-copilot**](recipes/by-use-case/trading-copilot/) | `beginner` + `production` + `eval` backtest | Market research + alerts (NOT auto-execution) on a watchlist + rule set. Cheap analyst + escalated skeptic + CoVe-style claim verification. Slack/Telegram/Discord webhooks or stdout. |

Plus one Rust case-study recipe under `by-pattern/`:

- [**rust-mcp-search-tool**](recipes/by-pattern/rust-mcp-search-tool/) — ~5 MB static MCP server wrapping SearXNG; demonstrates where Rust genuinely earns its place in the agent stack (and where it doesn't).

## The research-assistant stack — what's actually shipped

Five waves of techniques, each env-toggleable so leave-one-out ablations
are trivial. **135/135 unit tests green**, all mocked (no network or API
key required for `pytest`).

**Tier 1 — retrieval** (lives in `core/rag/`)
- BM25 + dense embeddings + Reciprocal Rank Fusion (`HybridRetriever`)
- Cross-encoder reranker (`CrossEncoderReranker`, `BAAI/bge-reranker-v2-m3`, lazy-loaded)
- Anthropic-style contextual chunking (`contextualize_chunks`)
- **Wave 5:** persistable local corpus (`CorpusIndex`) — index your own PDFs/md/txt/html

**Tier 2 — adaptive verification** (production tier)
- HyDE query rewriting, auto-gated on numeric queries
- Chain-of-Verification after synthesis
- Iterative retrieval bounded by `MAX_ITERATIONS`
- Self-consistency voting (opt-in)

**Tier 3 — reproducibility** (eval harness)
- 12-config ablation runner (`eval/ablation.py`)
- Pareto plotter (`eval/pareto.py`)
- Four metrics: factuality (LLM-judge), citation-accuracy, citation-precision, latency

**Tier 4 — 2026 SOTA layered on top**
- T4.1 ThinkPRM-style step-level critic after plan + search
- T4.2 FLARE active retrieval on hedged claims
- T4.3 Question classifier router → compute scales with difficulty
- T4.4 LLM-based evidence compression before synthesize
- T4.5 Plan refinement when critic rejects decomposition (opt-in)

**Wave 4 — local-first engine enhancements**
- W4.1 Cross-encoder rerank wired into `_retrieve` (two-stage retrieval)
- W4.2 Full-page fetch via `trafilatura` (snippets → clean article text)
- W4.3 Per-call observability trace (node, model, latency, tokens) — no SaaS

**Wave 5 — bring your own documents**
- W5.1 `LOCAL_CORPUS_PATH` — index your own PDFs / markdown / text / HTML via `scripts/index_corpus.py`; each sub-query pulls top-K matches from the local index alongside web results. Citations flow as `corpus://<source>#p<page>#c<chunk>`.

## Three ways to run it

```bash
git clone https://github.com/TheAiSingularity/agentic-ai-cookbook-lab
cd agentic-ai-cookbook-lab
```

**Mac, fully local (free):**
```bash
bash scripts/setup-local-mac.sh     # installs Ollama + gemma4:e2b + nomic-embed + SearXNG
cd recipes/by-use-case/research-assistant/beginner
make install
make smoke
```
On an Apple M4 Pro this runs end-to-end in ~40 s / beginner, ~95–175 s /
production query (bottleneck is the 2 B local model, not the framework —
infrastructure overhead is ~3%). Zero dollars.

**GPU VM (4× RTX 6000 Pro, self-hosted):**
```bash
bash scripts/setup-vm-gpu.sh --engine sglang --spec-dec \
  --model Qwen/Qwen3.6-35B-A3B
cd recipes/by-use-case/research-assistant/production
make smoke
```
Uses SGLang's RadixAttention prefix caching + EAGLE speculative
decoding. Expected 5–10× speedup over the Mac path with substantially
better answers — same code, just a bigger brain.

**OpenAI (pay-per-query):**
```bash
cd scripts/searxng && docker compose up -d
export OPENAI_API_KEY=sk-...
cd recipes/by-use-case/research-assistant/beginner && make install && make smoke
```
Same code. Different `OPENAI_BASE_URL`. ~$0.003–$0.004 / production
query at `gpt-5-mini` prices.

**Bring your own documents (optional, on top of any path above):**
```bash
# build a corpus from a directory of PDFs / markdown / text
python scripts/index_corpus.py build ~/papers --out ~/papers.idx
export LOCAL_CORPUS_PATH=~/papers.idx
make run Q="your question"
```

## Repo layout

```
recipes/
  by-use-case/
    research-assistant/      # beginner + production tiers, eval harness, 12-config ablation
    trading-copilot/         # beginner + production + backtest
  by-pattern/
    rust-mcp-search-tool/    # Rust case study

core/
  rag/                       # HybridRetriever · CrossEncoderReranker · contextualize_chunks · CorpusIndex

scripts/
  searxng/                   # docker-compose for self-hosted meta-search
  setup-local-mac.sh         # Mac dev stack (Ollama)
  setup-vm-gpu.sh            # Linux GPU stack (vLLM or SGLang, + optional EAGLE)
  index_corpus.py            # build / info / query a local corpus index

docs/
  how-it-works.md            # elevator pitches + SOTA comparison (read this first)
  progress.md                # wave-by-wave build log
  paper-draft.md             # arXiv tech report skeleton, methodology, ablation matrix

foundations/                 # OpenClaw / OpenShell / NemoClaw / Hermes Agent explainers
```

## Status

- **Waves 0 → 5 all shipped.** Wave 0 skeleton · Wave 0.5 SOTA-per-task pivot · Wave 1 research-assistant beginner · Wave 2 T1-T4 (full SOTA stack + ablation harness) · Wave 3 trading-copilot beginner + production + backtest · Wave 4 local-first engine (rerank wired + trafilatura fetch + observability trace) · Wave 5 local corpus indexing. See [`docs/progress.md`](docs/progress.md).
- **Pending:** run the 12-config ablation on the GPU VM with SimpleQA-100 + BrowseComp-Plus-50 to produce the paper's numbers.

## Contributing

Issues, recipe requests, and PRs welcome. See [`CONTRIBUTING.md`](CONTRIBUTING.md).
The recipe format is intentionally opinionated — each recipe ships
`main.py` + `requirements.txt` + `Makefile` + `test_*.py` + a `techniques.md`
with primary-source citations. No framework-comparison suites inside
recipes — one SOTA stack per task.

## Related

- [HermesClaw](https://github.com/TheAiSingularity/hermesclaw) — the secure runtime these recipes can run inside
- [NVIDIA/OpenShell](https://github.com/NVIDIA/OpenShell) — kernel-level agent sandbox
- [NousResearch/hermes-agent](https://github.com/NousResearch/hermes-agent) — self-improving agent

MIT licensed.
