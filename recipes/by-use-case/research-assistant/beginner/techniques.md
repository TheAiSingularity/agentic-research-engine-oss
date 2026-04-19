# Techniques — research-assistant/beginner

Every SOTA choice in this recipe, with a primary-source link. When a newer
benchmark changes the answer, update this file and the recipe together.

---

## Framework: LangGraph

**Why:** Lowest token overhead among 2026 Python agent frameworks for
stateful workflows. Graph nodes with direct state transitions avoid the
repeated chat-history passing that inflates token costs in loop-oriented
frameworks.

- [2026 AI Agent Framework Decision Guide (dev.to)](https://dev.to/linou518/the-2026-ai-agent-framework-decision-guide-langgraph-vs-crewai-vs-pydantic-ai-b2h)
  — LangGraph achieves the lowest latency and token usage in head-to-head
  benchmarks.
- [Same Chat App, 4 Frameworks (Medium)](https://medium.com/@kacperwlodarczyk/same-chat-app-4-frameworks-pydantic-ai-vs-langchain-vs-langgraph-vs-crewai-code-comparison-64c73716da68)
  — LangGraph ≈ 280 LoC; CrewAI ≈ 420 LoC with +18% token overhead for an
  equivalent 3-agent workflow.

## Web search: Exa (not Tavily, not Brave)

**Why:** Higher complex-retrieval accuracy, faster, and — critically for
agent cost — Exa's query-dependent *highlights* send 50–75% fewer tokens
to the LLM than shipping full page content.

- [Exa vs Tavily 2026](https://exa.ai/versus/tavily) — Exa scores 81% vs
  Tavily 71% on complex retrieval, runs 2–3× faster.
- [Best Web Search APIs for AI (Firecrawl 2026)](https://www.firecrawl.dev/blog/best-web-search-apis)
  — Exa's query-dependent highlights score 10% higher on RAG benchmarks
  than full-text retrieval while sending 50–75% fewer tokens.
- [Tavily alternatives roundup (WebSearchAPI.ai)](https://websearchapi.ai/blog/tavily-alternatives)
  — context on Tavily's Feb 2026 Nebius acquisition and roadmap uncertainty.

## Retrieval ranking: `core/rag` v0 (cosine), upgrading to hybrid + rerank

**Why v0 now:** Establishes the API surface recipes will depend on. Naive
cosine is a baseline that works well when your evidence set is already
query-focused (which Exa highlights is).

**Why v1 next:** SOTA retrieval in 2026 is a two-stage pipeline: hybrid
(BM25 + dense) with reciprocal-rank-fusion followed by cross-encoder
reranking on top-50. Benchmarked at Recall@5 0.816 and MRR@3 0.605,
outperforming all single-stage methods. Contextual retrieval at indexing
time reduces retrieval failures by up to 67%.

- [RAG review 2025–2026 (RAGFlow)](https://ragflow.io/blog/rag-review-2025-from-rag-to-context)
- [Benchmarking retrieval for financial docs (arXiv)](https://arxiv.org/html/2604.01733)
- [Advanced RAG patterns 2026 (dev.to)](https://dev.to/young_gao/rag-is-not-dead-advanced-retrieval-patterns-that-actually-work-in-2026-2gbo)

## LLM routing: Gemini 3.1 Flash-Lite default, GPT-5.4 mini for synthesis

**Why routing:** Sending simple tasks to Haiku-class models and harder ones
to more capable models reduces cost 50–80% while maintaining quality.

**Why Gemini 3.1 Flash-Lite as default:** $0.25 / $1.50 per M tokens,
1M context, 363 tok/s throughput. Independent analysis rates it the
strongest cheap-tier model for high-volume workloads in early 2026.

**Why GPT-5.4 mini for synthesis:** Highest agentic-task accuracy in the
budget tier. OSWorld-Verified 72.2, comfortably beating Claude Haiku 4.5
(57) and Gemini 3 Flash (53). Used only on the final synthesis step —
where reasoning quality matters most and token volume is smallest.

- [Artificial Analysis model leaderboard](https://artificialanalysis.ai/leaderboards/models)
- [LM Council Apr 2026 benchmarks](https://lmcouncil.ai/benchmarks)
- [BenchLM: Best Budget LLMs 2026](https://benchlm.ai/blog/posts/best-budget-llms-2026)
- [Gemini 3.1 Flash-Lite review (Bridgers)](https://bridgers.agency/en/blog/gemini-flash-lite-review)

## What nobody tells you

**Exa's `highlights=True` is doing most of the retrieval work.**
You often don't need a separate vector DB on top — you need it only when
you're combining evidence from *many* searches (which this recipe does,
because the planner fans out into 3 sub-queries). If your recipe runs a
single search, you can drop the `retrieve` node entirely and save the
embedding cost.
