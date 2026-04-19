# Progress Journal

## 2026-04-19
- Project created. Name locked: `TheAiSingularity/agentic-ai-cookbook-lab`.
- Wave 0 skeleton complete locally: directory tree, README, LICENSE, CONTRIBUTING, .gitignore, issue templates (3), CI workflow stubs (Python + Rust matrices), directory READMEs for core/, recipes/, foundations/, comparisons/, skills/, and per-recipe READMEs for the three Wave 1 flagships (research-assistant, youtube-analyzer, trading-copilot).
- Private repo pushed to GitHub as `TheAiSingularity/agentic-ai-cookbook-lab` (initial commit `791be65`). Topics + discussions + issues configured.
- **Wave 0.5 pivot same-day**: user clarified goal is "SOTA cookbooks for respective tasks, not a comparison suite." See DEC-006. Rewrote README, CONTRIBUTING, recipes/README, 3 per-recipe READMEs to drop the 4-framework matrix. Deleted 12 empty framework subdirs under each recipe's `beginner/`. Added `eval/` subdir per recipe. Updated issue template to require SOTA-stack rationale + citations. Reset `tasks.yaml` with SOTA-per-task tasks (T3–T11 + T13–T15).
- SOTA stacks chosen after April-2026 benchmark research: LangGraph + Exa + contextual-hybrid-rerank RAG + Gemini Flash-Lite routing for research-assistant; Pydantic AI + yt-dlp + Flash-Lite 1M context for youtube-analyzer; LangGraph + yfinance + RSS + Flash-Lite/GPT-5.4 mini routing for trading-copilot.
- Next: commit Wave 0.5 locally, push, then start Wave 1 with research-assistant/beginner as the canonical SOTA template.
- Task tracking: moved to Linear per the `.project/` Linear-first convention. YAML tracking files (`tasks.yaml`, `milestones.yaml`, `risks.yaml`, `sprints/current.yaml`) archived to `.project/archive/` as historical snapshot. The `.project/archive/tasks.yaml` reflects the Wave 1 task breakdown — use it as the source when creating Linear issues via `/new-task`.
