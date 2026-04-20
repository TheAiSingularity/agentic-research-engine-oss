# Plan — Gold-Standard Open-Source Local Research Engine

**Overwrites** the previous plan (Wave 3 trading-copilot, shipped long ago). This is a strategic pivot of the whole repo.

---

## Context

### What you asked for (synthesis of your message)

Build a **world-class open-source research engine** positioned as "the best $0 research agent that runs on a laptop," with:

- **Default stack**: Gemma 4 4B local via Ollama; no paid API required; API-key fallback available when a user opts in.
- **Distribution**: Claude plugin (official marketplace), MCP server (official registry), and community-aggregator listings. Repo goes **private** during active development.
- **Interfaces**: CLI + TUI + Web GUI, **all three in parallel** (your choice).
- **Self-learning**: trajectory logging + memory retrieval (your choice) — no LoRA in v1.
- **Transparency**: every LLM call, every source, every verification decision visible. Hallucination flagging UI.
- **Context compaction** when approaching the model's context limit.
- **Plugin / skill ecosystem**: load Claude plugins and Hermes skills from external sources.
- **Domain presets**: medical / academic-paper / financial / stock-trading / general — extensible.
- **Documentation**: 5+ worked research examples with real outputs; detailed contributor guide.
- **Repo rebrand**: the cookbook repo itself is rebranded (your choice).
- **Authorship**: commits authored by TheAiSingularity only, no other contributor lines going forward.

### Why this is a meaningful bet (from the competitive research)

The honest gap in April 2026: **nobody ships "offline-first local product + excellent UX + verified reasoning" in one package.**
- Perplexica (27 k★) has the UX but weak reasoning.
- Khoj (strong) focuses on personal knowledge, not deep research.
- MiroThinker-H1 (88.2 BrowseComp) is hosted-first, not productized for Mac.
- OpenResearcher-30B (54.8 BrowseComp-Plus) has the reasoning but no UX.
- gpt-researcher (25.7 k★) has an old architecture.
- Perplexity / OpenAI Deep Research / Google Deep Research / Kagi are all cloud-only and paid.

**Our wedge**: the first local-first research engine with full observability, CoVe-grade verification, multi-format plugin/skill support, and honest positioning — "runs on your laptop, costs nothing, shows you everything."

### Honest quality ceiling (from the same research)

Gemma 4 4B will be 15–25 % below 30 B+ open models on complex multi-hop reasoning. We **do not** claim to beat GPT-5.4 Pro. We claim to be the best $0 local research agent. That framing is load-bearing — promotional copy must reflect it.

---

## Locked decisions (from your AskUserQuestion answers)

| Decision | Your choice |
|---|---|
| Repo location | **Rebrand the cookbook repo itself** |
| Self-learning scope | **Trajectory logging + memory retrieval** (no LoRA in v1) |
| Interfaces | **CLI + TUI + Web GUI, all three in parallel** |

### Decisions still needed at execution time (not blocking this plan)

1. **Final project name** for the rebrand. Shortlist:
   - `agentic-research` (descriptive, clear positioning)
   - `open-research-engine` (risk: conflates with OpenResearcher-30B)
   - `researchlab` (short, memorable)
   - `ari` / `agentic-research-intelligence` (acronym play)
   - `freelance` (free + local + research; cheeky, works if you like it)
   - `reflective` (matches the plan filename's codename; meaningful for a verifying agent)
  
  **My default if you don't pick**: `agentic-research`. GitHub URL becomes `github.com/TheAiSingularity/agentic-research`.

2. **Co-Authored-By Claude lines on past commits** — leave as-is (recommended; rewriting history on a repo that was briefly public is destructive) or force-push a rewrite. Going forward, **no more Co-Authored-By Claude** regardless.

---

## What we reuse (don't rebuild)

| Asset | Where | Status |
|---|---|---|
| `core/rag/` v1 | `core/rag/python/` | Stable — `HybridRetriever`, `CrossEncoderReranker`, `contextualize_chunks`, `CorpusIndex`. 5 exports, 29 tests green. |
| Production research pipeline | `recipes/by-use-case/research-assistant/production/main.py` (826 LOC) | The engine core — 8 nodes, 30 env gates, trace infra, W6 hardening already in. Extract into modules. |
| Document-QA recipe | `recipes/by-use-case/document-qa/beginner/` | Becomes one of the domain presets (`domains/personal_docs.yaml`). Source of the 4-node minimal pipeline pattern. |
| Trading-copilot recipe | `recipes/by-use-case/trading-copilot/` | Becomes `domains/stock_trading.yaml` specialization via plugin system; safety-rail tests preserved. |
| Rust MCP case study | `recipes/by-pattern/rust-mcp-search-tool/` | Kept as a historical case study; the main MCP server for the engine is a new **Python** MCP that exposes the full `research` tool (not just search). |
| SearXNG + trafilatura + Ollama stack | `scripts/searxng/`, existing Ollama flow | No change. Still the zero-cost local default. |
| 159 mocked tests | `recipes/**/test_*.py` + `core/rag/tests/` | Grow to ~280+ as new code lands. |
| `docs/progress.md`, `docs/how-it-works.md` | `docs/` | Rewrite for the new positioning; keep the wave-by-wave history as an "origins" section. |

**Net reuse**: ~60 % of the final codebase is already written. This is not a greenfield project.

---

## Post-rebuild repo layout

```
<new-name>/                                  # repo renamed from agentic-ai-cookbook-lab
├── engine/                                  # NEW — the flagship engine
│   ├── core/
│   │   ├── pipeline.py                      # 8-node LangGraph extracted from current main.py
│   │   ├── models.py                        # model routing + small-model heuristic
│   │   ├── trace.py                         # W4.3 observability, extracted + enhanced
│   │   ├── memory.py                        # NEW — SQLite trajectory log + relevance retrieval
│   │   ├── compaction.py                    # NEW — context-window compaction when near limit
│   │   ├── domains.py                       # NEW — preset loader + config schema
│   │   ├── plugins.py                       # NEW — Claude-plugin + Hermes-skill loader
│   │   └── safety.py                        # NEW — forbidden-symbol + hallucination scan
│   ├── interfaces/
│   │   ├── cli.py                           # enhanced CLI (flags for --memory, --domain, --plugins, --trace-level, --api-key, --no-stream)
│   │   ├── tui.py                           # Textual-based TUI: live trace pane, source gallery, hallucination flags, plugin manager
│   │   └── web/                             # FastAPI + HTMX localhost GUI
│   │       ├── app.py
│   │       ├── templates/
│   │       └── static/
│   ├── mcp/
│   │   ├── server.py                        # Python MCP server — one `research` tool wrapping the full pipeline
│   │   └── claude_plugin/
│   │       ├── .claude-plugin/
│   │       │   └── plugin.json              # per plugins-reference spec
│   │       ├── skills/                      # bundled Claude skills (YAML + Markdown)
│   │       ├── agents/                      # optional agent definitions
│   │       └── README.md                    # plugin marketplace copy
│   ├── domains/
│   │   ├── medical.yaml
│   │   ├── papers.yaml
│   │   ├── financial.yaml
│   │   ├── stock_trading.yaml
│   │   ├── personal_docs.yaml
│   │   └── general.yaml
│   ├── examples/
│   │   ├── 01_medical_covid_treatment.md
│   │   ├── 02_paper_contextual_retrieval.md
│   │   ├── 03_financial_nvda_earnings.md
│   │   ├── 04_technical_rerank_comparison.md
│   │   └── 05_personal_pdf_summary.md
│   ├── benchmarks/                          # 4B-scale benchmark harness
│   │   ├── simpleqa_mini.jsonl
│   │   ├── browsecomp_mini.jsonl
│   │   ├── runner.py
│   │   └── RESULTS.md
│   ├── tests/                               # pytest for everything in engine/
│   ├── requirements.txt
│   ├── Makefile                             # install / smoke / test / cli / tui / gui / mcp / clean
│   └── README.md                            # engine-specific quickstart
├── core/rag/                                # UNCHANGED (v1 stable, 5 exports)
├── archive/
│   └── recipes/                             # current recipes/ moves here, kept as historical + cookbook-style examples
│       ├── by-use-case/                     # research-assistant + trading-copilot + document-qa archived
│       └── by-pattern/
├── scripts/
│   ├── searxng/                             # unchanged
│   ├── setup-local-mac.sh                   # unchanged
│   ├── setup-vm-gpu.sh                      # unchanged
│   └── index_corpus.py                      # unchanged (becomes engine-facing utility)
├── docs/
│   ├── architecture.md                      # NEW — deep technical spec
│   ├── plugins-skills.md                    # NEW — how to write/install plugins + skills
│   ├── domains.md                           # NEW — how to configure a domain preset
│   ├── self-learning.md                     # NEW — trajectory logging + memory model
│   ├── benchmarks.md                        # NEW — 4B-scale results, honest numbers
│   ├── progress.md                          # UPDATE — wave-by-wave appended
│   ├── how-it-works.md                      # REWRITE — new positioning
│   └── paper-draft.md                       # UPDATE — reframe around local-first
├── CONTRIBUTING.md                          # MAJOR REWRITE — encourages OSS PRs
├── CODE_OF_CONDUCT.md                       # NEW
├── README.md                                # REWRITE — new hero, new positioning
├── LICENSE                                  # unchanged (MIT)
└── .github/
    ├── workflows/                           # CI for tests, benchmark, plugin publish
    ├── ISSUE_TEMPLATE/                      # bug / feature / plugin-request
    └── PULL_REQUEST_TEMPLATE.md             # NEW
```

**Deletion note**: `recipes/` at the top level does *not* get deleted — it moves to `archive/recipes/` so all existing URLs in blog posts / commits still work via GitHub's permalink. The cookbook framing becomes "historical / examples" rather than the primary pitch.

---

## Phased delivery (realistic)

This is **3 to 6 months of work** at 1–3 sessions per week. Ship in order; each phase is independently valuable. Every phase ends with tests green + a working demo + a git tag.

### Phase 0 — Hygiene (this session)

Goal: clean baseline to build on; no irreversible decisions yet.

1. `gh repo edit --visibility private` — flip back to private.
2. `gh repo view` to confirm visibility, description still accurate.
3. Document the rebrand decision + propose names in `docs/progress.md` for your review.
4. **Stop Co-Authored-By Claude on go-forward commits** — adjust the session's commit conventions document (mental note; not code).
5. Run the full test suite once — establish the 159/159 baseline on this commit.

No code changes. **Ships this session.**

### Phase 1 — Engine core extraction + Gemma 4 4B characterization (1–2 sessions)

Goal: prove Gemma 4 4B is a viable default, extract the 826-LOC `main.py` into testable modules.

1. Install `gemma4:4b` via Ollama, verify it runs.
2. Run current production pipeline against gemma4:4b on our 3 canonical scenarios (A/B/C) + measure vs gemma4:e2b baseline. Numbers go in `engine/benchmarks/RESULTS.md`.
3. Extract `main.py` into `engine/core/{pipeline,models,trace}.py` without changing behavior. 8 nodes stay; env gates stay. **Must remain 159/159 green.**
4. Keep the current `production/main.py` as a thin re-export shim so the existing recipe still works (backwards compat).

Ships phase-1 tag when: new module layout + gemma4:4b numbers + 159/159 still green.

### Phase 2 — Memory + compaction (2 sessions)

Goal: persistent memory + context compaction without breaking the pipeline.

1. `engine/core/memory.py`:
   - SQLite-backed trajectory log: `{query_id, timestamp, question, domain, evidence[], intermediate_steps[], final_answer, cove_verified[], tokens, latency}`.
   - `--memory {off,session,persistent}` CLI flag.
   - On query start (if memory on): embed question, retrieve top-K semantically similar prior trajectories, inject summaries as additional context.
   - `engine reset-memory` CLI subcommand.
2. `engine/core/compaction.py`:
   - Track total input-token estimate across the pipeline state.
   - When nearing `CONTEXT_LIMIT_CHARS` (default ~24 k chars for 4 B models), run a compactor LLM pass that collapses older evidence into 1-sentence summaries while preserving URLs + CoVe-verified facts.
   - Env gates: `CONTEXT_LIMIT_CHARS`, `ENABLE_COMPACTION=1`.
3. New tests: `test_memory.py` (storage, retrieval, reset) + `test_compaction.py` (triggers at threshold, preserves verified facts, idempotent).

### Phase 3 — Three interfaces, in parallel (3–4 sessions)

Goal: CLI + TUI + Web GUI that all talk to the same engine core.

1. **CLI** (`engine/interfaces/cli.py`):
   - Flags: `--question`, `--domain`, `--memory`, `--plugins`, `--api-key`, `--model`, `--stream`, `--trace-level {summary,full}`, `--output {markdown,json}`.
   - `engine run` / `engine ask` / `engine reset-memory` / `engine domains list` / `engine plugins list` / `engine plugins install <uri>`.
2. **TUI** (`engine/interfaces/tui.py`, using `textual`):
   - Panes: question input, live synthesis (streaming tokens), source gallery (clickable evidence rows), trace timeline (per-node latency bars), hallucination flags (red/green indicators per CoVe claim), memory browser, plugin manager.
   - Keyboard-driven. Works over SSH. Pip-installable.
3. **Web GUI** (`engine/interfaces/web/`, FastAPI + HTMX + Jinja2):
   - Single-page layout at `localhost:8080`.
   - Left: query + domain selector. Right: tabbed panels for Answer / Sources / Trace / Hallucination-Check / Memory.
   - HTMX streams token-by-token (SSE or streaming HTML).
   - No auth; no cloud; never connects out.
4. All three share a `engine.interfaces.common` module for rendering (source cards, trace summaries, hallucination-flag widgets).

### Phase 4 — MCP + Claude plugin + marketplaces (2–3 sessions)

Goal: distribute the engine across all four ecosystems.

1. **Python MCP server** (`engine/mcp/server.py`, using official `mcp` Python SDK):
   - Single tool: `research({question, domain?, memory?, plugins?}) → {answer, sources[], verified_claims[], unverified_claims[], trace}`.
   - Stdio transport. Optional SSE transport for local HTTP clients.
2. **Claude plugin bundle** (`engine/mcp/claude_plugin/`):
   - `.claude-plugin/plugin.json` per `code.claude.com/docs/en/plugins-reference`.
   - Bundled skills: `research.md` (invokes the MCP), `cite-sources.md`, `verify-claim.md`, `set-domain.md`.
   - README with marketplace copy (screenshots, positioning, demo GIF).
3. **Submissions**:
   - `platform.claude.com/plugins/submit` — Anthropic official review.
   - `registry.modelcontextprotocol.io` — publish via `mcp-publisher`.
   - `claudemarketplaces.com`, `mcp.so`, `claudeskills.info` — community aggregators (flag as third-party, not official).
4. **Hermes-skill adapter**: convert our Claude skills to `agentskills.io` YAML format; document manual submission to HermesHub.

### Phase 5 — Plugin / skill loaders (2–3 sessions)

Goal: users can install third-party plugins + skills from external sources at runtime.

1. `engine/core/plugins.py`:
   - `engine plugins install <url>` — supports:
     - GitHub repo (`gh:owner/repo[@tag]`) → `git clone` + validate `plugin.json`.
     - URL to `marketplace.json` (per Claude plugin spec).
     - Local filesystem path.
   - Loader for Claude plugins: reads `plugin.json`, registers skills + MCP servers + hooks into the engine's plugin registry.
   - Adapter for Hermes skills (`agentskills.io` YAML) → internal skill format.
   - **Safety**: signature verification (if signed), sandboxed subprocess for hook execution, forbidden-symbols scan (reuse `engine/core/safety.py`), explicit user confirmation before any plugin runs untrusted code.
2. Plugin Manager UI in all three interfaces (list / install / remove / inspect).
3. Shipped with 3 example "starter plugins" to prove the system works.

### Phase 6 — Domain presets + 5 worked examples (2 sessions)

Goal: users pick a domain, get a tuned agent. Full examples documented.

1. `engine/domains/*.yaml` — each preset specifies:
   - Default search sources (SearXNG query filters, corpus paths, RSS feeds).
   - Prompt overrides (domain-specific synthesize instructions).
   - Verification thresholds (stricter for medical; looser for personal docs).
   - Specialized tools (`pubmed_search` for medical, `yfinance` for stock, etc.).
2. **5 worked examples** in `engine/examples/`, each a standalone Markdown file with:
   - The question
   - The `engine run` command used
   - The full trace (trimmed to highlights)
   - The sources retrieved
   - The final answer with citations
   - Verified vs unverified claims breakdown
   - Reproduction instructions (fresh clone → exact command → same output)
3. The examples also serve as integration tests (pytest fixture reproduces them against mocked LLMs).

### Phase 7 — Documentation + contributor onboarding (1–2 sessions)

Goal: a stranger can read the repo and submit a useful PR within a day.

1. **`README.md`** — rewritten hero, positioning, benchmarks table, install quickstart (one command), example output screenshot.
2. **`docs/architecture.md`** — deep technical spec: every node, every env var, the memory model, the compaction strategy, the plugin loading lifecycle.
3. **`docs/plugins-skills.md`** — step-by-step "write your first plugin" guide with a worked example.
4. **`docs/domains.md`** — "write your first domain preset" with a worked example.
5. **`docs/self-learning.md`** — trajectory schema, memory retrieval algorithm, opt-in/out mechanics, data-handling transparency.
6. **`docs/benchmarks.md`** — honest Gemma 4 4B numbers vs baseline vs premium; vs open competitors.
7. **`CONTRIBUTING.md`** major rewrite — "good first issues," PR template, review SLAs, plugin-submission lane, domain-preset-submission lane.
8. **`.github/ISSUE_TEMPLATE/`** + `PULL_REQUEST_TEMPLATE.md`.
9. **`CODE_OF_CONDUCT.md`** — standard Contributor Covenant.

### Phase 8 — Benchmark harness + public numbers (1–2 sessions)

Goal: claims are verifiable.

1. `engine/benchmarks/runner.py` reads jsonl fixtures, runs the pipeline against each question with the chosen config, writes per-question + aggregate results.
2. Mini-fixtures: `simpleqa_mini.jsonl` (20 Q), `browsecomp_mini.jsonl` (10 Q), `domain_specific_mini.jsonl` (5 per domain = 25 Q). Gold answers manually verified.
3. 12-config Pareto plot (rerank × fetch × compress × memory × domain).
4. Results committed to `engine/benchmarks/RESULTS.md` + referenced in the README.

### Phase 9 — Rebrand + public launch (1 session)

Goal: go public with the new name.

1. `gh repo rename <new-name>` (after user picks the name).
2. `gh repo edit --visibility public --accept-visibility-change-consequences`.
3. Update the repo description, homepage, topics.
4. Submit to Claude plugin marketplace + MCP registry.
5. Draft launch copy (HN / r/LocalLLaMA / Twitter).

---

## Technical choices (locked)

| Concern | Choice | Why |
|---|---|---|
| Orchestration | **LangGraph** | Already used; strong ecosystem fit; checkpointing supports our memory layer. |
| TUI framework | **Textual** | Pure Python, `pip install`, runs over SSH, strong widget ecosystem, MIT. Beats curses and blessed. |
| Web GUI | **FastAPI + HTMX + Jinja2** | No build step. Runs locally. Minimal dep surface. SSE-native for streaming. Matches the "runs anywhere" ethos. |
| MCP server | **Official Python `mcp` SDK** | Cleaner integration than the Rust case study for the full engine. Rust MCP stays as the educational example. |
| Memory store | **SQLite + `sentence-transformers` embeddings** | Zero-config; embed re-uses existing infra (`nomic-embed-text` via Ollama). No external DB. |
| Benchmark runner | **Pytest-style** | Reuse existing harness patterns; plugs into CI. |
| CI | **GitHub Actions** | Free for public repos; matrix tests across Python 3.11/3.12, runs mocked suite + smoke benchmarks weekly. |
| Default local model | **Gemma 4 4B** | Your choice. Existing W6 small-model heuristics already match this pattern. |
| API-key fallback | **Any OpenAI-compatible** | Existing `OPENAI_BASE_URL` / `OPENAI_API_KEY` plumbing works as-is; engine auto-detects and does not route to cloud unless user opts in via `--api-key`. |
| License | **MIT** | Unchanged. No AGPL drag (SearXNG runs out-of-process). |

---

## Verification

Each phase has a clear exit criterion. Overall smoke at the end of each phase:

1. **Tests**: `pytest` across `engine/`, `core/rag/`, and any remaining recipes. Target: 280+ by the end of Phase 6.
2. **Live smoke**: each interface (CLI, TUI, Web GUI) runs the same canonical question end-to-end against Ollama + SearXNG, produces a cited answer, and records a trajectory when memory is on.
3. **Benchmark**: Phase 8 publishes absolute numbers on Gemma 4 4B against mini fixtures. Expected floor: SimpleQA-Mini ≥ 70 %, BrowseComp-Mini ≥ 40 % verified-claims rate. If reality is worse by > 15 pts, we re-evaluate model choice.
4. **MCP + plugin**: Phase 4 verified by loading the Claude plugin into Claude Desktop and successfully invoking `research` end-to-end against the local engine.
5. **Plugin loader**: Phase 5 verified by installing and running one real third-party Claude plugin from the community marketplace.
6. **Examples reproducible**: Phase 6 verified by running each of the 5 examples on a fresh clone and confirming output matches the shipped Markdown (allowing for mocked-LLM determinism).

---

## Non-goals for v1 (honest)

- **Beating GPT-5.4 Pro or MiroThinker-H1 on BrowseComp.** We're a 4 B-class agent; we don't claim SOTA. We claim "best free local."
- **LoRA / model fine-tuning on Mac.** Deferred until Phase 10+ when we have GPU access (or until trajectory data volume justifies MLX LoRA).
- **Desktop app packaging (Tauri / Electron).** Web GUI serves the same role locally. Desktop bundling is a later phase.
- **Team collaboration / multi-user workspaces.** v1 is single-user, single-machine. Team features = v2+.
- **Hosted SaaS.** Not in v1. The Mac-local story is the entire v1 positioning.
- **General-web crawler / own search index.** We discussed and rejected this earlier; SearXNG stays. A curated ARI-style index is a v2+ consideration.
- **Mobile app.** Out of scope.

---

## Risks + mitigations

| Risk | Mitigation |
|---|---|
| Gemma 4 4B is worse than expected on domain-specific queries | Phase 1 measures this directly; if numbers are bad, fall back to gemma4:e2b or Qwen 2.5 3 B, document honestly in `docs/benchmarks.md`. |
| Three interfaces in parallel → none gets polished | Phase 3 has weekly check-ins; if one interface falls behind, cut scope on it rather than delay the others. TUI is the critical-path one (richest debug view). |
| Claude plugin review rejects us | Anthropic submission has no SLA; run the MCP registry + community aggregators in parallel so distribution isn't single-point-of-failure. |
| Plugin loader security (untrusted code execution) | Default-deny; explicit user confirmation per plugin; forbidden-symbols scan; sandboxed subprocess; never auto-install. |
| 3–6 month timeline slips | Each phase is independently valuable and tagged. We can stop at any phase boundary and still have shipped something useful. |
| Rebrand breaks links | Near-zero impact (repo was public for ~2 hours with 0 stars); GitHub auto-redirects old repo URLs. |

---

## Execution order summary (this session vs later)

**This session (if you approve):** Phase 0 only — flip repo private, verify tests, commit the plan file itself to the repo. Ends clean. No irreversible work.

**Next session(s):** Phase 1 (engine extraction + Gemma 4 4B numbers). This is the first real build phase.

**Beyond:** Phases 2–9 in order, 1–3 sessions each, weekly cadence. Each phase is committed + tagged + verifiably working before the next one starts.

---

## Open decisions needed before Phase 9 (but not blocking earlier phases)

1. **Final project name** (I default to `agentic-research` if you don't specify). Changeable any time before Phase 9's rebrand.
2. **Whether to rewrite git history** to remove Co-Authored-By Claude from past commits (I default to leaving them; going-forward commits are clean).
3. **Whether to submit to third-party aggregators** (`claudemarketplaces.com`, `mcp.so`, etc.) in addition to the official channels. My default: yes, for discoverability, with the caveat that these are unofficial.
