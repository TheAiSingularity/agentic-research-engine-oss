# Example 04 — Technical: cross-encoder reranker vs contextual retrieval

Domain: `papers` · Expected wall-clock on Mac M4 Pro: ~90 s. Chosen because it's a multi-concept technical comparison that exercises CoVe iteration.

## The question

> How does using a cross-encoder reranker (like BAAI/bge-reranker-v2-m3)
> compare to Anthropic's Contextual Retrieval for improving RAG
> pipeline recall? What does the research suggest about combining them?

## Command

```bash
make cli Q="How does using a cross-encoder reranker (like BAAI/bge-reranker-v2-m3) compare to Anthropic's Contextual Retrieval for improving RAG pipeline recall? What does the research suggest about combining them?" --domain papers --memory persistent
```

## What the pipeline does on hard multi-concept questions

This question has been through three live runs during the engine's development (see `docs/progress.md` Wave 6 / Wave 8):

| run | config | answer quality |
|---|---|---|
| Baseline (Wave 4) | gemma4:e2b, no W6 prompt | rambling essay on reranker side only |
| W6 binary | gemma4:e2b + binary refuse clause | clean refusal but over-refused |
| **W6 refined (now default)** | **gemma3:4b + three-case prompt** | **structured partial answer with explicit gap flagging** |

The W6 refined prompt (documented in `DEC-012`) handles this case by:

1. Answering the reranker side from evidence (bge-reranker-v2-m3 exists, how it re-scores, published numbers).
2. Answering the Anthropic-Contextual-Retrieval side from evidence (49 % / 67 % figures).
3. If evidence lacks a direct comparison study, **explicitly saying so** rather than fabricating one.

## Expected output shape

```
Q: How does using a cross-encoder reranker compare to Anthropic's
   Contextual Retrieval for improving RAG pipeline recall? …

[class: synthesis]

A: The evidence supports the following for each approach individually:

   **Cross-encoder reranker (BAAI/bge-reranker-v2-m3) [1][2]:**
   Cross-encoder reranking re-scores (query, passage) pairs with full
   attention and picks the highest-ranked candidates from a hybrid
   retriever's top-N pool. Published benchmarks [2] report Recall@5
   0.816 and MRR@3 0.605 when layered on BM25 + dense hybrid
   retrieval — noticeably better than any single-stage approach.

   **Anthropic Contextual Retrieval [3]:**
   Contextual Retrieval prepends each chunk with a 1-2 sentence
   LLM-generated summary of where it fits in its source document,
   before BM25 and embedding indexing. Anthropic reports a 49 %
   reduction in retrieval failures over plain chunking, rising to
   67 % when combined with a reranker [3].

   **On combining them:**
   Anthropic's own blog [3] demonstrates the combination explicitly —
   contextual chunking feeds into hybrid retrieval, then a cross-
   encoder reranker picks the final top-K. The reported 67 % failure
   reduction is the combined figure.

   The evidence does not contain a head-to-head comparison where each
   technique is tested in isolation against a consistent benchmark
   beyond Anthropic's own measurements. Independent reproduction is
   recommended if the 49 % vs 67 % distinction is load-bearing for a
   production decision.

Cited sources:
  [1] ● https://huggingface.co/BAAI/bge-reranker-v2-m3
  [2] ● https://arxiv.org/abs/2604.01733   (hybrid+rerank benchmark)
  [3] ● https://www.anthropic.com/news/contextual-retrieval

Hallucination check — 6/6 claims verified
  ✓ BAAI/bge-reranker-v2-m3 re-scores (query, passage) pairs with attention
  ✓ Hybrid+rerank Recall@5 0.816 matches cited paper
  ✓ Hybrid+rerank MRR@3 0.605 matches cited paper
  ✓ Anthropic reports 49% failure reduction for Contextual Retrieval alone
  ✓ Anthropic reports 67% when combined with reranking
  ✓ Anthropic's blog demonstrates the combination explicitly

Trace (per-node totals):
  search      31.5 s  (4 subqueries incl. FLARE re-search on hedged sentence)
  compress   12.0 s  (evidence pool ~10k chars post-fetch)
  fetch_url  11.8 s
  synthesize  9.3 s
  verify      7.1 s
  plan        5.9 s
  classify    3.0 s
  retrieve    0.8 s

  total: 81.4 s · ~19k tokens · iterations=1
```

## When this example exercises the memory layer

With `--memory persistent`, the answer to this question becomes context for related follow-ups:

```
/research How does HyDE compare to contextual retrieval for the same metric?
```

…triggers a memory hit on Example 04's trajectory (cosine similarity ≥ 0.55 by default) and prepends a short summary to the new question. The follow-up benefits from the already-verified claims about the 49 % / 67 % figures without re-searching.

Memory hits are surfaced in the TUI right panel and the web GUI's trace-pane "Memory hits" section.
