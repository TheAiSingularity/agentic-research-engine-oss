# Contributing

Thanks for your interest. This repo is a **runnable recipe gallery with framework comparisons** — contributions should follow that format so the collection stays coherent.

## The rules that don't bend

1. **Every beginner recipe runs in ≤60s from a fresh clone via `make run`.** Longer than that = doesn't ship.
2. **Every beginner recipe is ≤100 lines and heavily commented** so a newcomer can read the whole thing in one sitting.
3. **Every recipe README answers three questions, in this order:** What does it do? Who is it for? Why would you use it?
4. **Framework comparisons are the same task, four ways.** Not four different tasks. Comparisons only make sense when the task is held constant.
5. **No AI-generated fluff** in foundations or comparison pages. Primary sources, cited links, real opinions.

## Adding a new recipe

Use the existing `research-assistant/` as your template. Every recipe directory needs:

```
recipes/by-use-case/<recipe-name>/
├── README.md                 # What / Who / Why, plus the badge line
├── recipe.yaml               # Metadata (used by the gallery regenerator)
├── beginner/
│   ├── <framework>/          # One subdir per framework — vanilla, langgraph, crewai, ...
│   │   ├── main.py
│   │   ├── requirements.txt
│   │   ├── Makefile          # Must have a `run` target
│   │   └── README.md         # One paragraph: what this specific impl demonstrates
│   └── ...
├── comparison.md             # The benchmark table across framework impls
└── production/               # Optional — opt-in for flagship recipes
```

Open an issue with the **recipe-request** template first so the scope is agreed before you write code.

## Adding a production tier

Only graduate a recipe to the `production/` tier when:
- The beginner version is stable and used as a reference.
- You can add at least three of: tests, observability (Logfire / OpenTelemetry), HermesClaw compose file, `.env.example` with real-life secrets, a runbook, SLO/cost/latency numbers in the README.
- The production tier imports from `core/` rather than duplicating shared code.

## Adding a foundation or comparison page

Both follow the three-question opener (What / Who / Why) and include one **"What nobody tells you"** callout — the contrarian or non-obvious observation that separates the page from docs-style competitors.

## `core/` contributions

`core/rag/`, `core/memory/`, `core/tools/`, and `core/sandbox/` are the shared library. Changes here must:
- Keep a clean public API (we're building toward a potential standalone spin-out for `core/rag/`).
- Ship with tests in `core/<module>/tests/`.
- Not break any recipe that depends on them (CI runs every recipe).

## Code style

- Python: f-strings, type hints, pathlib, 4-space indentation. Minimal comments — well-named identifiers first.
- Rust: standard rustfmt. Clippy clean.
- No comments explaining WHAT the code does. Only WHY, and only when the why is non-obvious.

## The PR checklist

- [ ] `make run` works from a fresh clone in ≤60s (beginner)
- [ ] `pytest` green (production)
- [ ] README answers What / Who / Why
- [ ] Recipe metadata (`recipe.yaml`) updated
- [ ] If adding a framework impl: `comparison.md` has the benchmark row
- [ ] Links check with `markdown-link-check`
