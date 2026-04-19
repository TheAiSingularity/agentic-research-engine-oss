<p align="center">
  <!-- banner.png goes here in Wave 1 -->
  <strong>agentic-ai-cookbook-lab</strong>
</p>

<p align="center">
  <a href="LICENSE"><img src="https://img.shields.io/badge/license-MIT-blue.svg" alt="License"></a>
  <img src="https://img.shields.io/badge/status-wave%200-orange.svg" alt="Status">
  <img src="https://img.shields.io/badge/recipes-3-green.svg" alt="Recipes">
  <img src="https://img.shields.io/badge/frameworks-4%20per%20recipe-green.svg" alt="Frameworks">
  <img src="https://img.shields.io/badge/languages-python%20%2B%20rust-green.svg" alt="Languages">
</p>

**Clone-and-run agent apps — every recipe built with 4 frameworks side by side, so you can see how they actually compare.**

Each recipe works end-to-end in under a minute from a fresh clone. Framework comparisons aren't opinion pieces — they're the same task, shipped four ways, benchmarked on code clarity, tokens, latency, cost, and accuracy.

The default sandboxed runtime is [HermesClaw](https://github.com/TheAiSingularity/hermesclaw) — Hermes Agent inside NVIDIA OpenShell, kernel-enforced. Every production-tier recipe ships with a HermesClaw compose file.

---

## The three flagship recipes (Wave 1)

| Recipe | What it does | Frameworks compared |
|---|---|---|
| [research-assistant](recipes/by-use-case/research-assistant/) | Answers research questions with web search + RAG + tool-calling | vanilla · langgraph · crewai · llamaindex |
| [youtube-analyzer](recipes/by-use-case/youtube-analyzer/) | Pulls transcripts, detects chapters, summarizes, suggests titles | vanilla · langgraph · crewai · pydantic-ai |
| [trading-copilot](recipes/by-use-case/trading-copilot/) | Market research + alerts (research tool — NOT auto-execution) | vanilla · langgraph · openai-agents-sdk · dspy |

Each recipe has a `comparison.md` with the benchmark table. That's the page you'll want to read.

---

## Repo layout

```
recipes/       # Runnable recipes, organized by use-case and by pattern
core/          # Shared library: rag · memory · tools · sandbox
foundations/   # Plain-English explainers: OpenClaw · OpenShell · NemoClaw · Hermes Agent
comparisons/   # Framework face-offs, protocol deep-dives
skills/        # Hot category — reusable agent skills
```

## Levels

Every recipe declares which levels exist:

- **`beginner/`** — ≤100 lines, heavily commented, `make run` in ≤60 seconds. **Every recipe has this.**
- **`production/`** — real tests, observability, HermesClaw compose, SLO/cost numbers. **Opt-in — flagship recipes only.**
- **`rust/`** — for categories where Rust genuinely wins (MCP servers, inference runtimes, tool binaries, edge agents).

## Running a recipe

```bash
git clone https://github.com/TheAiSingularity/agentic-ai-cookbook-lab
cd agentic-ai-cookbook-lab/recipes/by-use-case/research-assistant/beginner/vanilla
make run
```

## Status

This is **Wave 0** — skeleton only. Wave 1 (3 recipes × 4 framework impls + 4 foundations pages + `core/rag/` v0) ships next.

See the [plan](#) for the full roadmap.

---

## Related

- [HermesClaw](https://github.com/TheAiSingularity/hermesclaw) — the secure runtime these recipes run inside
- [NVIDIA/OpenShell](https://github.com/NVIDIA/OpenShell) — the sandbox underneath HermesClaw
- [NousResearch/hermes-agent](https://github.com/NousResearch/hermes-agent) — the agent

MIT licensed.
