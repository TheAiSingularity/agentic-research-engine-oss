# `core/rag/` — SOTA retrieval

Every recipe that needs retrieval-augmented generation imports from here
rather than rolling its own. The goal is to collect the retrieval
techniques that actually move the accuracy needle in 2026 — not just
"embed + cosine similarity."

## What's shipped

### v0 — naive baseline (`Retriever`)

Plain dense retrieval: OpenAI `text-embedding-3-small` + cosine similarity.
Exists so recipes always have *something* to import. Two-function API:
`index(docs)` returns a retriever; `retriever.retrieve(query, k)` returns
ranked docs.

### v1 — SOTA hybrid stack (ships now)

- **`HybridRetriever`** — BM25 + dense + Reciprocal Rank Fusion (RRF, `k=60`).
  Sparse catches exact tokens / rare strings / numbers that dense misses;
  dense catches paraphrase. RRF fuses ranks without needing score
  normalization.
- **`CrossEncoderReranker`** — second-stage re-scorer using
  `BAAI/bge-reranker-v2-m3`. Lazy-imports `sentence-transformers` so
  callers can skip the dep if they only want hybrid retrieval.
- **`contextualize_chunks`** — prepends a short LLM-generated context
  paragraph to each chunk before embedding / BM25 indexing. Anthropic's
  technique; reduces retrieval failures by 35–67% on their benchmarks.

### The 2026 two-stage SOTA pipeline

```
raw chunks
    │
    │  contextualize_chunks (optional, +35–67% accuracy at index time)
    ▼
HybridRetriever.retrieve(query, k=50)   ← stage 1 (recall)
    │
    ▼
CrossEncoderReranker.rerank(query, candidates, k=8)   ← stage 2 (precision)
```

Benchmarked: Recall@5 0.816, MRR@3 0.605 (vs single-stage baselines); ~25%
reduction in downstream synthesis tokens because top-8 is tighter.

## Usage

```python
from core.rag import HybridRetriever, CrossEncoderReranker, contextualize_chunks, make_openai_llm
from openai import OpenAI

client = OpenAI()

# Optional: contextualize chunks at index time
chunks_ctx = contextualize_chunks(full_doc, chunks, make_openai_llm(client, "gpt-5-nano"))

# Stage 1: hybrid recall
h = HybridRetriever()
h.add(chunks_ctx)
candidates = h.retrieve(query, k=50)

# Stage 2: cross-encoder precision
reranker = CrossEncoderReranker()  # lazy-loads bge-reranker-v2-m3 on first call
top = reranker.rerank(query, candidates, k=8)
```

## Benchmarks

See [`BENCHMARKS.md`](BENCHMARKS.md) for live numbers (refreshed per release).

## Graduation candidate

This module is the leading candidate for spin-out into a standalone
`TheAiSingularity/agentic-rag` repo once the API stabilizes and recipes
prove out. See [../README.md](../README.md) for the graduation criteria.
