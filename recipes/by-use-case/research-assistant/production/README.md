# research-assistant/production

Same pipeline as `beginner/`, plus four adaptive-verification techniques
that target the hardest questions. This tier exists because single-pass
answering fails on multi-hop / ambiguous queries. Keep `beginner/` for
teachability; ship `production/` when quality matters.

## What's added on top of beginner

| Node / technique | Effect | When it runs | Gated by |
|---|---|---|---|
| **HyDE** in `_plan` | Generates a hypothetical answer per sub-query; uses its embedding for retrieval | Every plan pass | `ENABLE_HYDE=1` (default); auto-skipped on numeric/factoid queries |
| **CoVe** in `_verify` | Extracts standalone claims from the answer; verifies each against evidence independently; flags unsupported claims | After synthesize | `ENABLE_VERIFY=1` (default) |
| **Iterative retrieval** (ITER-RETGEN) | Re-searches *for failed claims only* and regenerates | When verify flags unverified claims | Bounded by `MAX_ITERATIONS` (default 2) |
| **Self-consistency** in `_synthesize` | Samples N candidates; picks the one with the best citation-grounding score | Every synthesize | `ENABLE_CONSISTENCY=1` (opt-in; costs N× synthesize) |

### Pipeline

```
plan (+HyDE) → search → retrieve → synthesize → verify (CoVe)
      │                                              │
      │                         verified ──yes──▶ END
      │                                              │
      │                                              no
      └── iterate (re-search failed claims, bounded) ┘
```

Easy questions exit in one pass (~same latency as beginner). Hard
questions get 2–3 extra LLM calls (verify + regenerate) and occasionally
one iteration of re-search for unverified claims.

## Run

Same env contract as `beginner/` plus the four knobs below. With your
local Ollama stack:

```bash
export OPENAI_BASE_URL=http://localhost:11434/v1
export OPENAI_API_KEY=ollama
export MODEL_PLANNER=gemma4:e2b
export MODEL_SEARCHER=gemma4:e2b
export MODEL_SYNTHESIZER=gemma4:e2b
export MODEL_VERIFIER=gemma4:e2b       # CoVe — cheap model is fine
export EMBED_MODEL=nomic-embed-text
export SEARXNG_URL=http://localhost:8888

# Toggles (defaults shown)
export ENABLE_HYDE=1
export ENABLE_VERIFY=1
export MAX_ITERATIONS=2
export ENABLE_CONSISTENCY=0
export CONSISTENCY_SAMPLES=3

make install
make run Q="your hard multi-hop research question"
```

On a GPU VM with vLLM/SGLang, point `OPENAI_BASE_URL` at `:8000/v1` and
set the model names to real tags (`Qwen/Qwen3.6-35B-A3B`, etc.).

## Test

```bash
make test   # mocked; no API key or network needed
```

## Sandboxed execution (HermesClaw)

Once `core/sandbox` lands, `compose.yml` here will boot the full
pipeline inside a HermesClaw sandbox so network egress and filesystem
access are policy-enforced. Placeholder for now.

## Expected cost / latency

| Question type | Extra calls vs beginner | Added latency |
|---|---|---|
| Easy, fully-verified first pass | +1 (verify) | +10–30s |
| Unverified → one iteration | +1 search + +1 synth + +1 verify | +30–90s |
| Hard + self-consistency enabled | N× synth + N× verify | 2–3× baseline |

All still $0 on a fully-local rig. On paid OpenAI: roughly 2× beginner's
per-query cost when iteration triggers.

## See also

- [`beginner/`](../beginner/) — the lean reference implementation (100 LOC)
- [`eval/`](../eval/) — benchmark harness (SimpleQA-100 + BrowseComp-Plus-50
  land with Tier 3)
- [`../../../core/rag/`](../../../core/rag/) — retrieval primitives used here
