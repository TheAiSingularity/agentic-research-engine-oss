# engine/

The flagship research engine. 8-node LangGraph pipeline (`classify → plan →
search → retrieve → fetch_url → compress → synthesize → verify`) with W4
local-first enhancements, W6 small-model hardening, and W7 streaming
synthesis. Runs fully local on Mac M4 Pro with Gemma 3 4 B + Ollama + SearXNG,
or against any OpenAI-compatible endpoint via `OPENAI_BASE_URL`.

---

## Layout

```
engine/
├── core/                       ← pipeline, models, trace (Phase 1 ✓)
│   ├── pipeline.py             the 8 nodes + build_graph
│   ├── models.py               LLM plumbing + small-model heuristic
│   ├── trace.py                W4.3 observability
│   ├── memory.py               Phase 2 — SQLite trajectory + retrieval
│   ├── compaction.py           Phase 2 — context compaction
│   ├── domains.py              Phase 6 — preset loader
│   └── plugins.py              Phase 5 — external plugin/skill loader
├── interfaces/                 ← Phase 3
│   ├── cli.py
│   ├── tui.py                  Textual TUI
│   └── web/                    FastAPI + HTMX GUI
├── mcp/                        ← Phase 4
│   ├── server.py               Python MCP server exposing `research` tool
│   └── claude_plugin/          bundled .claude-plugin/plugin.json + skills
├── domains/                    ← Phase 6 — YAML presets
├── examples/                   ← Phase 6 — 5 worked research examples
├── benchmarks/                 ← Phase 8 — mini SimpleQA + BrowseComp fixtures
│   └── RESULTS.md              honest measured numbers
├── tests/
├── requirements.txt
├── Makefile                    install / test / cli / tui / gui / mcp / smoke / bench
└── README.md                   you're reading it
```

---

## Quickstart

### Mac local (Gemma 3 4 B via Ollama, $0 per query)

```bash
bash ../scripts/setup-local-mac.sh    # if not already done
ollama pull gemma3:4b                 # 3.3 GB
cd engine && make install
make smoke                            # end-to-end on the canonical question
```

Expected wall-clock on M4 Pro: **~45 s** per query with all defaults.

### OpenAI cloud (opt-in)

```bash
export OPENAI_API_KEY=sk-...
export MODEL_PLANNER=gpt-5-nano MODEL_SYNTHESIZER=gpt-5-mini …
make smoke
```

---

## Configuration

All env vars documented in the header of `engine/core/pipeline.py`.
Defaults are tuned for Gemma 3 4 B on Mac. See also
[`benchmarks/RESULTS.md`](benchmarks/RESULTS.md) for measured numbers.

| Env | Default | Purpose |
|---|---|---|
| `OPENAI_BASE_URL` | unset (OpenAI) | swap to `http://localhost:11434/v1` for Ollama |
| `OPENAI_API_KEY` | `ollama` | sentinel for local; real key for cloud |
| `MODEL_SYNTHESIZER` | `gpt-5-mini` | drives small-model heuristic |
| `TOP_K_EVIDENCE` | auto | 5 on small models, 8 otherwise |
| `ENABLE_RERANK` | `0` | opt-in; first run downloads bge-reranker-v2-m3 (~560 MB) |
| `ENABLE_FETCH` | `1` | trafilatura full-page fetch |
| `ENABLE_STREAM` | `1` | stream tokens to stdout |
| `ENABLE_TRACE` | `1` | per-call observability, summary printed at end |
| `LOCAL_CORPUS_PATH` | unset | set to an index dir to augment SearXNG with your own docs |

Full list + semantics: `engine/core/pipeline.py` module docstring.

---

## How the pipeline works

![pipeline diagram placeholder]

1. **classify** — route question into {factoid, multihop, synthesis}
2. **plan** — decompose into sub-queries (+ optional HyDE expansion)
3. **search** — SearXNG meta-search + optional local corpus hits (parallel)
4. **retrieve** — hybrid BM25 + dense + RRF, optional cross-encoder rerank
5. **fetch_url** — trafilatura clean-text extraction of top pages
6. **compress** — LLM distillation + per-chunk char cap
7. **synthesize** — streamed answer generation with citations
8. **verify** — CoVe claim extraction + evidence check; iterates if any fail

All eight nodes are env-toggleable for leave-one-out ablation.

---

## Tests

```bash
make test                        # mocked; no API key or network needed
```

Target: 159+ green. Current recipe tests (research-assistant/trading-copilot/
document-qa) still pass unchanged via the `production/main.py` shim that
re-exports from `engine.core`.

---

## Next phases

- **Phase 2** — memory persistence + context compaction
- **Phase 3** — CLI + TUI + Web GUI (all three in parallel)
- **Phase 4** — MCP server + Claude plugin + marketplace submissions
- **Phase 5** — plugin / skill loader (Claude plugins + Hermes skills)
- **Phase 6** — domain presets (medical / papers / financial / stock / general)
- **Phase 7** — docs + contributor guide
- **Phase 8** — benchmark harness + public numbers
- **Phase 9** — rebrand + public launch

See [`.project/plans/research-engine-master-plan.md`](../.project/plans/research-engine-master-plan.md).
