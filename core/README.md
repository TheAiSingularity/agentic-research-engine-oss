# `core/` — shared library

Reusable primitives that power recipes across the cookbook. Every module ships with tests and has a stable public API. Modules are candidates for graduation into standalone repos once they prove out.

| Module | Purpose | Status |
|---|---|---|
| [`rag/`](rag/) | SOTA retrieval — hybrid search, reranking, contextual retrieval, GraphRAG, late-interaction | Wave 1 v0 |
| [`memory/`](memory/) | Persistent-memory patterns (Mem0-style) for agents that remember across sessions | Wave 3 |
| [`tools/`](tools/) | Tool registry + MCP helpers + schema patterns | Wave 3 |
| [`sandbox/`](sandbox/) | HermesClaw integration glue — run any recipe inside the sandbox with one import | Wave 2 |

## Language layout

Each module has parallel `python/` and `rust/` implementations **only** where the Rust version adds real value (performance, portability, binary size). Most modules will be Python-first with Rust variants for specific categories — see `<module>/README.md` for specifics.

## Graduation

When a `core/` module hits:
- Used by ≥20 recipes, **or**
- Clean API stable across 2+ release waves, **or**
- Community PRs specifically targeting it

…it becomes a candidate for spin-out into its own repo. `core/rag/` is the leading graduation candidate.
