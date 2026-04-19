# Progress Journal

## 2026-04-19
- Project created. Name locked: `TheAiSingularity/agentic-ai-cookbook-lab`.
- Wave 0 skeleton complete locally: directory tree, README, LICENSE, CONTRIBUTING, .gitignore, issue templates (3), CI workflow stubs (Python + Rust matrices), directory READMEs for core/, recipes/, foundations/, comparisons/, skills/, and per-recipe READMEs for the three Wave 1 flagships (research-assistant, youtube-analyzer, trading-copilot).
- Private repo pushed to GitHub as `TheAiSingularity/agentic-ai-cookbook-lab` (initial commit `791be65`). Topics + discussions + issues configured.
- **Wave 0.5 pivot same-day**: user clarified goal is "SOTA cookbooks for respective tasks, not a comparison suite." See DEC-006. Rewrote README, CONTRIBUTING, recipes/README, 3 per-recipe READMEs to drop the 4-framework matrix. Deleted 12 empty framework subdirs under each recipe's `beginner/`. Added `eval/` subdir per recipe. Updated issue template to require SOTA-stack rationale + citations. Reset `tasks.yaml` with SOTA-per-task tasks (T3–T11 + T13–T15).
- SOTA stacks chosen after April-2026 benchmark research: LangGraph + Exa + contextual-hybrid-rerank RAG + Gemini Flash-Lite routing for research-assistant; Pydantic AI + yt-dlp + Flash-Lite 1M context for youtube-analyzer; LangGraph + yfinance + RSS + Flash-Lite/GPT-5.4 mini routing for trading-copilot.
- Next: commit Wave 0.5 locally, push, then start Wave 1 with research-assistant/beginner as the canonical SOTA template.
- Task tracking: moved to Linear per the `.project/` Linear-first convention. YAML tracking files (`tasks.yaml`, `milestones.yaml`, `risks.yaml`, `sprints/current.yaml`) archived to `.project/archive/` as historical snapshot. The `.project/archive/tasks.yaml` reflects the Wave 1 task breakdown — use it as the source when creating Linear issues via `/new-task`.
- Linear issues created (THE-86 done, THE-87 through THE-97 — Wave 1 queue). Wave 0.5 pushed as commit `846246f`.

## 2026-04-19 (evening) — Wave 1 first recipe shipped

- **THE-87 + THE-88 + THE-89 + THE-95 completed end-to-end.** Research-assistant beginner recipe is runnable and testable.
- `core/rag/` v0 built: Python package with `Retriever` / `index()` / `retrieve()` public API, OpenAI text-embedding-3-small default, pluggable embedder for testing. 5 unit tests green (mocked embedder, no API key needed).
- `recipes/by-use-case/research-assistant/beginner/main.py` built as LangGraph agent: 99 lines, plan → search → retrieve → synthesize. Model routing: Gemini 3.1 Flash-Lite for planning, GPT-5.4 mini for synthesis. Exa search with query-dependent highlights.
- Scaffolding: `Makefile` (run / smoke / test / install / clean), `requirements.txt`, `README.md`, `techniques.md` (primary-source citations for every SOTA choice), `test_main.py` (6 unit tests, all mocked — green).
- Eval harness seeded: `eval/dataset.jsonl` (3 starter questions — the full 10 land alongside closing THE-89), `scorer.py` (LLM-as-judge factuality + citation-precision), `Makefile` for `make eval`.
- **Total 11 tests green** across core/rag (5) and recipe (6).
- Live smoke test not executed — EXA/GOOGLE/OPENAI API keys not in session env. User can run `make smoke` locally after setting keys.
