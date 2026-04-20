# Example 02 — Academic paper: how Contextual Retrieval works

Domain: `papers` · Expected wall-clock on Mac M4 Pro: ~50 s. This is the scenario we benchmarked in Phase 1 (`benchmarks/RESULTS.md`) — reproducible as an integration test.

## The question

> What is Anthropic's Contextual Retrieval and what percentage reduction in retrieval failures did they report?

## Command

```bash
make cli Q="What is Anthropic's Contextual Retrieval and what percentage reduction in retrieval failures did they report?" --domain papers
```

Or via plugin:

```
/set-domain papers
/research What is Anthropic's Contextual Retrieval and what percentage reduction in retrieval failures did they report?
```

## Verified output (from Phase 1 live run, 2026-04-20)

```
Q: In what year did Anthropic introduce Contextual Retrieval, and what
   percentage reduction in retrieval failures did they report?

[class: multihop]

A: Contextual Retrieval was introduced by Anthropic [1]. It reduced the
   number of failed retrievals by 49% and, when combined with reranking,
   by 67% [1].

Verified: 3/3 claims  (iterations: 1)

── trace summary (15 entries, 48.66s total, ~17061 tokens) ──
  by node:
    search        calls= 4  latency= 14.71s  tokens~2366
    fetch_url     calls= 1  latency= 11.53s  tokens~0
    compress      calls= 1  latency=  7.00s  tokens~10144
    plan          calls= 5  latency=  5.04s  tokens~928
    verify        calls= 1  latency=  3.47s  tokens~1682
    classify      calls= 1  latency=  3.26s  tokens~112
    synthesize    calls= 1  latency=  2.97s  tokens~1829
    retrieve      calls= 1  latency=  0.69s  tokens~0
```

## What the `papers` preset contributes

Beyond the generic pipeline:

- **seed_queries** push SearXNG toward `site:arxiv.org`, `site:semanticscholar.org`, `site:openreview.net` — so the search stage pulls primary-source papers and preprints rather than blog posts.
- **top_k_evidence: 10** — paper research benefits from wider evidence coverage than general search.
- **min_verified_ratio: 0.70** — below 70 % CoVe-verified, the answer is flagged.
- **prompt_extra** asks for per-paper Contribution / Method / Results / Limitations blocks when multiple papers are cited.

On this particular question, the Anthropic blog post dominates the evidence pool (it's a product announcement, not a paper), so the answer is blog-shaped rather than a paper-by-paper breakdown. The structure kicks in more visibly for questions like "Compare Contextual Retrieval, HyDE, and FLARE" where multiple papers are relevant.

## Reproduction via integration test

```python
# engine/tests/test_examples.py — Phase 6 exit criterion
def test_example_02_reproduces_against_mocked_pipeline(patched_graph):
    result = run_query(
        "What is Anthropic's Contextual Retrieval and what percentage "
        "reduction in retrieval failures did they report?",
        domain="papers",
    )
    # Mocked pipeline always returns "Final answer [1]." — the test
    # verifies the pipeline was invoked with the papers preset active
    # (LOCAL_CORPUS_PATH / TOP_K_EVIDENCE overrides visible in the state).
```

Live reproduction with matching numbers requires the SearXNG federation to return the Anthropic blog as a top result (it usually does; if not, the answer content may vary but its **shape + CoVe-verified structure** is reproducible).
