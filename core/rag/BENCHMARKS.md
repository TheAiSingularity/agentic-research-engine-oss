# Retrieval benchmarks — `core/rag`

Benchmark numbers and methodology for each version. Live numbers come from
the research-assistant `eval/` harness; the reference numbers come from
published 2026 literature.

## Reference numbers (from literature)

**Two-stage hybrid + cross-encoder rerank, text+table corpora (arXiv 2604.01733):**

| Method                                   | Recall@5 | MRR@3 |
|------------------------------------------|:---:|:---:|
| BM25 only                                | 0.68 | 0.44 |
| Dense only (text-embedding-3-small)      | 0.72 | 0.48 |
| Hybrid (BM25 + dense + RRF)              | 0.79 | 0.57 |
| **Hybrid + cross-encoder rerank (top-50 → top-5)** | **0.82** | **0.61** |

**Anthropic contextual retrieval (2024 blog post):**
- Contextual embeddings alone: −35% retrieval failures vs baseline chunked embeddings
- Contextual embeddings + contextual BM25: −49%
- Plus cross-encoder rerank on top-50: **−67% retrieval failures**

## Live numbers (this repo)

### v0 (`Retriever`) — naive dense baseline

Measured on the research-assistant recipe's 3-question seed eval set
(`recipes/by-use-case/research-assistant/eval/dataset.jsonl`). Retrieval
quality isn't isolated — it's entangled with the end-to-end synthesis
pipeline. Use `citation_accuracy_mean` as a proxy for retrieval quality.

*Populated in Week 3 (ablation run) — placeholder.*

### v1 (`HybridRetriever` + optional rerank + optional contextual)

*Populated in Week 3 (ablation run) — placeholder.*

## Methodology

- **Dataset:** SimpleQA-100 + BrowseComp-Plus-50 subsets (land in Week 3).
- **Metrics:** Recall@k, MRR@k for retrieval; factuality + citation
  accuracy + latency + tokens for end-to-end.
- **Ablation matrix:** leave-one-out across {BM25, dense, rerank,
  contextual} to quantify each technique's marginal contribution.
- **Runner:** `recipes/by-use-case/research-assistant/eval/ablation.py`
  (lands Week 3).
