"""core.rag — shared retrieval primitives (v0 Python baseline).

Public API is the Python implementation. A future `core.rag.rust` submodule
may land for perf-sensitive recipes; it will expose the same surface.
"""

from .python import Retriever, index, retrieve

__all__ = ["Retriever", "index", "retrieve"]
__version__ = "0.0.1"
