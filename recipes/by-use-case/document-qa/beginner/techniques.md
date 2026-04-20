# document-qa techniques

The third flagship recipe. Demonstrates that `core.rag.CorpusIndex` and
`HybridRetriever` compose cleanly for a bring-your-own-documents use
case — no web search, no iteration, no compressor, no router.

## Why these four nodes (and only these four)

`document-qa` is deliberately the simplest of the three flagship recipes.
The question-answering loop on a fixed corpus doesn't need most of the
machinery that pays off for open-web research:

- **No router** — every query uses the same compute budget; factoid vs
  synthesis isn't a useful distinction when the corpus is bounded.
- **No iteration / FLARE** — you can't materially re-search a fixed
  corpus by rephrasing; the evidence set is what it is.
- **No compressor** — `PER_CHUNK_CHAR_CAP` at retrieve time is enough.
- **No web search** — explicit by design; the test suite asserts
  `searxng`, `trafilatura.fetch_url`, and `requests.get` do not appear
  in `main.py`.

What we do keep: **hybrid retrieval** (BM25 + dense + RRF via
`HybridRetriever`), **CoVe verification** (CoVe pattern from the
research-assistant production tier), and **streaming synthesis** (W7
UX polish — tokens print live).

## Sources

- `core/rag/python/corpus.py` — the `CorpusIndex` this recipe is built on.
- `core/rag/python/hybrid.py` — `HybridRetriever`, BM25 + dense + RRF.
- Anthropic 2024 — *Introducing Contextual Retrieval* — −35 to −67%
  retrieval-failure reduction when chunks carry doc-level context.
  `contextualize_chunks` is opt-in at index build time.
- Dhuliawala et al. 2023 — *Chain-of-Verification Reduces Hallucination
  in Large Language Models*.
- RAGFlow review 2026; arXiv 2604.01733 on two-stage retrieval benchmarks.

## Upgrade paths (not shipped beginner-side, deliberately)

- **Cross-encoder rerank** — the research-assistant production tier
  already wires `CrossEncoderReranker`. Adding it here would be a one-
  line swap: retrieve top-50 from hybrid, rerank to top-`TOP_K`. Defer
  until a production tier is demanded.
- **Contextualize at build time** — wire `contextualize_chunks` into
  `CorpusIndex.build`. Requires one LLM call per chunk at index time.
  Cheap on a GPU VM; slow on gemma4:e2b.
- **Multi-corpus fusion** — attach several `CorpusIndex` paths,
  retrieve from each, fuse with RRF. Useful when users want "my papers
  PLUS company docs PLUS my notes" in one query.
