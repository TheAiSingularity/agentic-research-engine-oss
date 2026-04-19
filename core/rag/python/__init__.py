"""core.rag — shared retrieval primitives for agentic-ai-cookbook-lab recipes.

v0 (Wave 1): naive baseline — OpenAI embeddings + cosine similarity.
v1 (Wave 2): Anthropic contextual retrieval + BM25 + dense hybrid + cross-encoder rerank.

Public API (stable across versions):
    Retriever         — simple class wrapping index + retrieve
    index(docs)       — index a list of strings, returns a Retriever
    retrieve(query, k, retriever) — retrieve top-k docs for a query

See ../README.md for the full roadmap and graduation criteria.
"""

from .rag import Retriever, index, retrieve

__all__ = ["Retriever", "index", "retrieve"]
__version__ = "0.0.1"
