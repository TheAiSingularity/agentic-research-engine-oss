# Example 05 — Personal docs: Q&A over your own PDF library

Domain: `personal_docs` · Expected wall-clock on Mac M4 Pro: ~35 s. No web access; strictly local.

## Setup (one-time)

```bash
# 1. Drop any mix of PDFs / markdown / .txt / HTML into a directory
mkdir -p ~/my-research-library
cp ~/Downloads/some-paper.pdf ~/my-research-library/
cp ~/Notes/my-notes.md ~/my-research-library/
# ... etc

# 2. Build the corpus index (one-time; embeddings via Ollama nomic-embed-text)
OPENAI_BASE_URL=http://localhost:11434/v1 \
OPENAI_API_KEY=ollama \
EMBED_MODEL=nomic-embed-text \
python scripts/index_corpus.py build ~/my-research-library --out ~/my-research.idx

# 3. Point the engine at the index
export LOCAL_CORPUS_PATH=~/my-research.idx
```

## The question

> Summarize what the papers in my library say about hybrid retrieval
> versus dense-only retrieval. Cite the specific sources.

## Command

```bash
make cli Q="Summarize what the papers in my library say about hybrid retrieval versus dense-only retrieval. Cite the specific sources." --domain personal_docs
```

## What the `personal_docs` preset does

- **No web search.** The preset has empty `searxng_categories` and the synthesize prompt_extra explicitly says "every citation MUST be a `corpus://` URL."
- **Evidence comes from `LOCAL_CORPUS_PATH` only.** The pipeline's `_search` augments with corpus hits; `_fetch_url` correctly skips `corpus://` URLs (they're already full chunks, not snippets).
- **Slightly relaxed verification** (`min_verified_ratio: 0.60`). Personal corpora are often sparse on any given topic; a 60 % floor avoids over-refusing when partial evidence is expected.
- **Smaller evidence budget** (`top_k_evidence: 6`). Personal corpora rarely need 10 chunks.

## Expected output shape

```
Q: Summarize what the papers in my library say about hybrid retrieval
   versus dense-only retrieval. Cite the specific sources.

[class: synthesis]

[corpus] loaded 187 chunks from ~/my-research.idx

A: Your library contains three sources that discuss this comparison:

   **Hybrid retrieval (BM25 + dense + RRF) vs dense-only:**
   According to your copy of the RAGFlow review [1], hybrid retrieval
   outperforms dense-only across every benchmark cited in the paper.
   BM25 catches exact-token matches that dense embeddings miss,
   especially for rare strings, numbers, and code identifiers [1].

   Your Anthropic Contextual Retrieval notes [2] add that hybrid
   retrieval alone reduces retrieval failures by ~35 %, but rises to
   ~49 % when BM25 and dense are combined via Reciprocal Rank Fusion
   (RRF k=60) as Contextual Retrieval specifies.

   Your notes on the 2604.01733 paper [3] report Recall@5 0.816 and
   MRR@3 0.605 for hybrid+rerank vs. lower numbers for dense-only;
   the paper argues that RRF's score-normalization is what makes
   hybrid robust across heterogeneous query types.

Cited sources:
  [1] ○ corpus://ragflow-review-2026.md#c14
  [2] ○ corpus://anthropic-contextual-retrieval-notes.md#c7
  [3] ○ corpus://2604-01733-hybrid-retrieval-benchmarks.pdf#p3#c22

Hallucination check — 4/4 claims verified
  ✓ Your RAGFlow review notes BM25+dense outperforms dense-only
  ✓ BM25 complements dense on rare tokens (per your notes)
  ✓ Contextual Retrieval combines BM25 + dense via RRF k=60 (per your notes)
  ✓ Hybrid+rerank Recall@5 0.816 (per your 2604.01733 notes)

Trace (per-node totals):
  corpus       0.6 s  (local index lookup, 6 chunks retrieved)
  synthesize   9.7 s
  verify       8.1 s
  compress     7.3 s
  plan         5.2 s
  classify     2.9 s
  retrieve     0.5 s
  fetch_url    0.1 s  (all corpus:// URLs skipped by design)

  total: 34.5 s · ~8200 tokens · iterations=1
```

## Citation format for corpus sources

`corpus://<source>#p<page>#c<chunk>` — the same format the main production pipeline uses when `LOCAL_CORPUS_PATH` is set. `○` denotes "not fetched over the network" (which is correct for personal docs — the text IS the corpus chunk).

## Privacy properties

- **No outbound network requests.** The pipeline detects empty SearXNG seed_queries + non-empty `LOCAL_CORPUS_PATH` and skips the SearXNG HTTP call entirely.
- **Embedding for retrieval is local too** — via Ollama's `nomic-embed-text`. If you've set `EMBED_MODEL=text-embedding-3-small` without disabling the key, the query embedding would go to OpenAI; users who insist on air-gapped operation should keep the default.
- **Memory entries from personal-docs queries are tagged `domain=personal_docs`** in the SQLite memory store — easy to wipe separately with a WHERE-clause query if desired.

## Testing

The end-to-end flow is exercised by `test_retrieve_shapes_corpus_urls_with_page_and_chunk` in the shipped document-qa recipe tests and by `test_search_merges_corpus_hits_into_evidence` in the production tests. Both run mocked; a live test requires rebuilding a fixture corpus but otherwise matches.
