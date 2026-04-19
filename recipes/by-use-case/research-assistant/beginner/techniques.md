# Techniques — research-assistant/beginner

Every SOTA choice in this recipe, with a primary-source link. When a newer
benchmark changes the answer, update this file and the recipe together.

---

## Framework: LangGraph

**Why:** Lowest token overhead among 2026 Python agent frameworks for
stateful workflows. Graph nodes with direct state transitions avoid the
repeated chat-history passing that inflates token costs in loop-oriented
frameworks. Clean fit for `plan → search → retrieve → synthesize`.

- [2026 AI Agent Framework Decision Guide (dev.to)](https://dev.to/linou518/the-2026-ai-agent-framework-decision-guide-langgraph-vs-crewai-vs-pydantic-ai-b2h)
  — LangGraph achieves the lowest latency and token usage in head-to-head benchmarks.

## Inference: OpenAI-compatible endpoint (portable)

**Why:** Every modern LLM server — OpenAI's own API, Ollama, vLLM, Groq,
Together — exposes the same `/v1/chat/completions` shape. The recipe
depends only on that interface (via the `openai` Python SDK), so
switching between paid cloud, on-prem GPU, and Apple-Silicon local
inference is one env var: `OPENAI_BASE_URL`.

The local paths use:
- **Ollama** (macOS / dev) — simplest to run on Apple Silicon; good at mid-size open-weight models
- **vLLM** (Linux GPU) — highest-throughput open-source inference server; tensor-parallel across multiple GPUs

- [Ollama OpenAI-compat docs](https://github.com/ollama/ollama/blob/main/docs/openai.md)
- [vLLM OpenAI-compat server](https://docs.vllm.ai/en/latest/serving/openai_compatible_server.html)

## Web search: SearXNG (self-hosted meta-search)

**Why:** No paid API key. No rate limits you didn't set yourself.
SearXNG queries DuckDuckGo, Bing, Wikipedia, arXiv, and ~80 other
engines in parallel and aggregates results. JSON API makes it a drop-in
replacement for Exa / Tavily / Brave. Running it in Docker on `:8888`
adds one `docker compose up` to setup.

The recipe's `search` node fetches SearXNG results and then asks the
searcher LLM to summarize them with inline `[N]` citations. That pattern
is deterministic, eval-friendly (you can hold search fixed and vary the
LLM), and works identically across every backend.

- [SearXNG project](https://github.com/searxng/searxng)
- [SearXNG JSON API docs](https://docs.searxng.org/user/search_api.html)

## Retrieval ranking: `core/rag` v0 (cosine), upgrading to hybrid + rerank

**Why v0 now:** Establishes the API surface recipes will depend on. Naive
cosine is fine when the evidence set is already query-focused (true here
— each sub-query's summary is already scoped to that sub-query).

**Why v1 next:** SOTA retrieval in 2026 is a two-stage pipeline — hybrid
(BM25 + dense) with reciprocal-rank-fusion, followed by cross-encoder
reranking on top-50. Benchmarked at Recall@5 0.816 and MRR@3 0.605,
outperforming all single-stage methods. Contextual retrieval at indexing
time reduces retrieval failures by up to 67%.

- [RAG review 2025–2026 (RAGFlow)](https://ragflow.io/blog/rag-review-2025-from-rag-to-context)
- [Benchmarking retrieval for financial docs (arXiv)](https://arxiv.org/html/2604.01733)
- [Advanced RAG patterns 2026 (dev.to)](https://dev.to/young_gao/rag-is-not-dead-advanced-retrieval-patterns-that-actually-work-in-2026-2gbo)

## LLM routing (three-tier)

**Why routing:** Sending simple tasks to a cheap tier and harder tasks
to a more capable tier reduces cost 50–80% without measurable quality
loss on the overall workflow.

- **Plan** is one short LLM call producing a list of sub-queries. A
  nano / 2B-class model handles it fine.
- **Search** summarizes 5 results per sub-query with citations. Needs
  reasoning and citation discipline — mid-tier model is the sweet spot.
- **Synthesize** is the final answer over all kept evidence. Needs the
  strongest reasoning available — mid-tier or above.

Pick the exact model names via `MODEL_PLANNER` / `MODEL_SEARCHER` /
`MODEL_SYNTHESIZER`. Defaults match OpenAI SKUs that exist today.

- [Artificial Analysis model leaderboard](https://artificialanalysis.ai/leaderboards/models)
- [LM Council benchmarks](https://lmcouncil.ai/benchmarks)

## Parallel fan-out

**Why:** The search step runs one call per sub-query, each doing a
SearXNG query + LLM summarization. Serial fan-out of 3 sub-queries is
~3× slower than necessary. We parallelize with `ThreadPoolExecutor` (not
async) because the `openai` SDK's sync client is thread-safe and
threading is the minimum complexity increment for IO-bound parallelism.

## What nobody tells you

**The cheapest agent in 2026 is one that runs on your own GPU.**
OpenAI's `web_search` tool, Tavily, Exa — all priced per call. At
hobby volume they're trivial. At production scale, every per-query fee
compounds. A vLLM + SearXNG rig on a workstation pays zero marginal
cost per query after setup. That's the reason this recipe's defaults
are local-first: we optimize for *zero-marginal-cost* research at the
edge where agents actually get used — iterative experimentation, eval
loops, long-running research jobs.
