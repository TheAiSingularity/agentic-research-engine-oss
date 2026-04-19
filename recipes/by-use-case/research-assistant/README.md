# research-assistant

**Levels:** beginner ⬛ · production ⬛ · rust ⬛ · **all pending — ships in Wave 1**

## What it does
Answers research questions by combining web search, page-fetching, and an LLM reasoning loop. Given a question like "what are the tradeoffs between ColBERT and BGE rerankers in 2026?", it searches, reads, synthesizes, and produces a cited answer.

## Who it's for
Anyone who wants to see what tool-calling + RAG actually looks like end-to-end, without the framework layers getting in the way. Also for anyone comparing agent frameworks on a fair benchmark — this recipe is the canonical single-agent RAG + tool-calling baseline.

## Why you'd use it
- Clone it, swap the LLM / embedding model / retriever, and you have a custom research tool.
- Read the `comparison.md` to see which framework produced the cleanest code for the same task.
- Graduate to `production/` when you want observability, caching, and a HermesClaw-sandboxed version.

## Framework implementations (Wave 1)

| Variant | Why this framework |
|---|---|
| [`beginner/vanilla/`](beginner/vanilla/) | Baseline — just OpenAI tool-calling loop, no framework. See the logic directly. |
| [`beginner/langgraph/`](beginner/langgraph/) | Graph-based — shows stateful reasoning as explicit nodes and edges |
| [`beginner/crewai/`](beginner/crewai/) | Multi-agent — researcher + fact-checker + writer working together |
| [`beginner/llamaindex/`](beginner/llamaindex/) | RAG-first — shows the framework's retrieval sweet spot |

## See also
- [`comparison.md`](comparison.md) — benchmark table across the four implementations (lands Wave 1)
- [`core/rag/`](../../../core/rag/) — the retrieval module this recipe pulls from
