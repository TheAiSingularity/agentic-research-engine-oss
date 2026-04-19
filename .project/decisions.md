# Decisions

## DEC-001 — Format: runnable recipe gallery, not tutorial series
**Date:** 2026-04-19
**Context:** Initial framing was "tutorial series / handbook" explaining OpenClaw, OpenShell, Hermes Agent, NemoClaw, plus the broader ecosystem. Tested against real GitHub data: pure tutorial / link-list repos plateau at 300–1.3K stars. Runnable-recipe repos (`Shubhamsaboo/awesome-llm-apps`: 106K⭐ / 15% fork-to-star ratio) dominate interaction in this category.
**Decision:** Pivot to clone-and-run recipe gallery. Foundations (4 pages) and comparisons (6 pages) stay as SEO support — not the headline.
**Consequences:** Higher interaction ceiling. Every recipe must `make run` in ≤60s from a fresh clone or it doesn't ship. CI load grows with recipe count.

## DEC-002 — Three flagship recipes for Wave 1, not fifty
**Date:** 2026-04-19
**Context:** Original scope was 50+ recipes. User pushed back: ship 3 first, prove the format, then scale.
**Decision:** Wave 1 ships **three recipes**: research-assistant, youtube-analyzer, trading-copilot. Each shipped in **four framework implementations** (plus vanilla baseline) to showcase side-by-side comparison. Twelve runnable impls total.
**Consequences:** Faster to first real ship. Framework comparison becomes a Wave 1 deliverable rather than a nice-to-have. Recipe count grows iteratively.

## DEC-003 — Python + Rust, strategic not parallel
**Date:** 2026-04-19
**Context:** Original plan was Python + TypeScript. User clarified: Rust, not TS.
**Decision:** Python is universal across all recipes. Rust is clustered in categories where it genuinely wins: MCP servers, inference runtimes, tool binaries, edge agents, sandbox-escape research. Target ~50 Python recipes / ~10–15 Rust recipes over the full roadmap — not 1:1 parity.
**Consequences:** Differentiated positioning (no serious agent-recipe repo exists in Rust). Lower maintenance cost than naive parity. TypeScript is deliberately out of scope.

## DEC-004 — Single repo with core/ graduation path, not two repos
**Date:** 2026-04-19
**Context:** User asked whether RAG should be its own repo. Analysis: two repos up front = 2× setup, halved network effect, premature abstraction.
**Decision:** Shared `core/` library inside this repo (rag / memory / tools / sandbox). Recipes import from `core/` rather than duplicating. Graduate `core/rag/` into a standalone `TheAiSingularity/agentic-rag` repo when it hits traction criteria (≥1K stars on this repo, ≥20 recipes using it, stable API across 2 waves).
**Consequences:** Cross-promotion between recipes and core library. Cleaner API via real-usage pressure before spin-out. Later fork is a 2-hour job, not an architectural migration.

## DEC-005 — Name: agentic-ai-cookbook-lab
**Date:** 2026-04-19
**Context:** Iterated through multiple candidate names. User wanted descriptive, okay-with-collisions, lab vibe. Target form: "agentic AI recipe/cookbook + lab."
**Decision:** `TheAiSingularity/agentic-ai-cookbook-lab`. Zero star-weighted GitHub collisions, descriptive (every keyword earns its keep), matches user's phrasing.
**Consequences:** URL is 23 characters — long but clean. "Agentic" keyword pulls in high-intent 2026 search traffic. "Cookbook" signals the content format. "Lab" signals experimentation / comparison.
