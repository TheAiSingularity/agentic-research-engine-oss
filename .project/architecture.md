# Architecture

## The model

Three concentric layers, each with a clear purpose and a clear relationship to the others:

```
┌──────────────────────────────────────────────────────────┐
│  foundations/ · comparisons/ — SEO support, reading path │
│                                                          │
│  ┌──────────────────────────────────────────────────┐    │
│  │  recipes/ — the headline. Every recipe:          │    │
│  │   - runs in ≤60s (beginner)                      │    │
│  │   - ships in 4 framework variants for comparison │    │
│  │   - imports from core/ where it makes sense      │    │
│  │                                                  │    │
│  │  ┌────────────────────────────────────────┐      │    │
│  │  │  core/ — shared library                │      │    │
│  │  │   rag · memory · tools · sandbox       │      │    │
│  │  │   graduation candidates for spin-out   │      │    │
│  │  └────────────────────────────────────────┘      │    │
│  └──────────────────────────────────────────────────┘    │
└──────────────────────────────────────────────────────────┘
                         │
                         │ production-tier recipes run inside
                         ▼
        ┌──────────────────────────────────────┐
        │  HermesClaw (separate repo)          │
        │  Hermes Agent + NVIDIA OpenShell     │
        │  kernel-enforced sandbox runtime     │
        └──────────────────────────────────────┘
```

## Recipe anatomy

```
recipes/by-use-case/<name>/
├── README.md                     # What / Who / Why + level badges
├── recipe.yaml                   # Machine-readable metadata (gallery regenerator input)
├── beginner/
│   └── <framework>/              # vanilla · langgraph · crewai · ...
│       ├── main.py               # Single file, ≤100 lines, comments explain WHY
│       ├── requirements.txt
│       ├── Makefile              # MUST define `make run` target
│       └── README.md             # One paragraph on what this impl demonstrates
├── comparison.md                 # Benchmark table across the framework impls
└── production/                   # Opt-in. Imports from core/. Real tests, obs, HermesClaw compose.
```

## core/ contract

Every `core/<module>/` exposes:
- A stable public API at the module root (`core.rag.retrieve`, `core.memory.store`, etc.)
- Python implementations under `python/`, Rust under `rust/` (where applicable)
- Tests under `tests/`
- A `README.md` with scope, status, and graduation readiness

Recipes depend on `core/` via import. Core modules never depend on recipes.

## CI model

- `recipe-ci.yml` — Python matrix (3.11, 3.12) + Rust stable. Discovers every `Makefile` with a `run` target and invokes it with a timeout. Broken recipes block merge.
- `link-check.yml` — `markdown-link-check` on push + weekly schedule.
- Cost-capped LLM keys in CI secrets.

## Cross-repo relationship with HermesClaw

HermesClaw is the **default production runtime**. Not a hard dependency — every recipe's beginner tier runs standalone. But every **production-tier** recipe includes a `compose.yml` that boots the recipe inside HermesClaw's sandbox.

The `core/sandbox/` module is the glue layer that makes this one-import:

```python
from core.sandbox import run_in_hermesclaw
run_in_hermesclaw(agent, policy="gateway")
```
