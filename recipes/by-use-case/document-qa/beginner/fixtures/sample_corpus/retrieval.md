# Retrieval techniques in the cookbook

## Hybrid retrieval

The first stage of retrieval combines BM25 (sparse, token-level) with dense
embeddings (semantic, vector-level) using Reciprocal Rank Fusion with k=60.
BM25 catches exact tokens, rare strings, numbers, and URLs that dense
embeddings miss. Dense catches paraphrases and semantic matches that BM25
misses. RRF fuses the two rank lists without having to normalize scores
across methods.

Implementation lives in `core/rag/python/hybrid.py` as `HybridRetriever`.
Usage: `.add(docs)` to index, `.retrieve(query, k=50)` to query.

## Cross-encoder reranking

The second stage re-scores (query, passage) pairs with full cross-attention
using `BAAI/bge-reranker-v2-m3` (Apache 2.0, multilingual). Benchmarks in
the RAG literature report Recall@5 0.816 and MRR@3 0.605 when reranker is
layered on top of hybrid retrieval — noticeably better than any single
stage alone.

Model is lazy-loaded on first call to avoid import-time cost. ~560MB
download on first run from Hugging Face; cached afterward. If the model
can't load for any reason the pipeline gracefully falls back to hybrid-
only retrieval.

## Contextual chunking

Before indexing, each chunk gets a 1-2 sentence LLM-generated summary of
where it fits in the source document prepended. This restores referents
("the company" → "Anthropic", etc.) that get lost when chunks are split
from their context. Anthropic's published benchmarks report a 35% to 67%
reduction in retrieval failures depending on configuration.

Implementation lives in `core/rag/python/contextual.py` as
`contextualize_chunks`. It's opt-in — you call it before `.add()`.

## Local corpus

The `CorpusIndex` class wraps `HybridRetriever` with on-disk persistence
and source-tracked chunks. Readers for PDF (via pypdf), markdown, text,
and HTML (via trafilatura) are shipped. Chunking is paragraph-aware with
character-window overlap for long paragraphs.

The CLI `scripts/index_corpus.py` exposes build/info/query subcommands.
The production research-assistant recipe can attach a local index via
`LOCAL_CORPUS_PATH`; corpus hits merge into evidence alongside web
results and are cited as `corpus://<source>#p<page>#c<chunk>`.
