# `core/rag/` — SOTA retrieval

Every recipe that needs retrieval-augmented generation imports from here rather than rolling its own. The goal is to collect the retrieval techniques that actually move the accuracy needle in 2026 — not just "embed + cosine similarity."

## What this module will cover

- **Hybrid search** — BM25 + dense retrieval with reciprocal rank fusion
- **Reranking** — cross-encoder or late-interaction (ColBERTv2-style)
- **Contextual retrieval** — Anthropic's 2024 technique, still state-of-the-art for corpus chunking
- **GraphRAG** — entity + community-level retrieval for corpus-wide questions
- **Multi-vector / late-interaction** — ColBERT-class retrievers for precision
- **Query rewriting & HyDE** — retrieval-time query augmentation

## Status

**Wave 1 v0:** naive RAG (embed + cosine) in `python/` — baseline so recipes can import something.
**Wave 2 v1:** hybrid search + reranking.
**Wave 3+:** contextual retrieval, GraphRAG.

## Benchmarks

`BENCHMARKS.md` will hold published numbers once v1 ships — naive vs hybrid vs hybrid+rerank, measured on a fixed eval corpus.

## Graduation candidate

This module is the leading candidate for spin-out into a standalone `TheAiSingularity/agentic-rag` repo once the API stabilizes and recipes prove out. See [`../README.md`](../README.md) for the graduation criteria.
