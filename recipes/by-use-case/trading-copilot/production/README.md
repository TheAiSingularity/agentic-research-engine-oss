# trading-copilot/production

Adaptive-verification tier on top of [`../beginner/`](../beginner/).
Same disclaimer: **research + alerts only, NOT auto-execution.**

## What's added on top of beginner

| Technique | Effect | Gated by |
|---|---|---|
| **T4.1 · Step critic** (`_critic`) | ThinkPRM-style judge after `gather` (coverage) and `analyze` (candidate quality); feedback written to `state["critic_notes"]` | `ENABLE_STEP_VERIFY=1` (default) |
| **T2 · Self-consistency skeptic** (`_skeptic` + `_skeptic_vote`) | Sample N skeptic verdicts per candidate, majority vote. Adaptive: N=1 on high-severity short-reason candidates, N=CONSISTENCY_SAMPLES otherwise | `ENABLE_CONSISTENCY=1` (default), `CONSISTENCY_SAMPLES=3` |
| **T2 · CoVe-style alert verification** (`_verify_alerts`) | Decompose each alert's reasoning into atomic claims; check each against raw prices + news; drop the alert if any claim is unsupported | `ENABLE_VERIFY=1` (default) |
| **Optional social layer** (`_fetch_social` via PRAW) | Pull recent Reddit mentions from configured subreddits; augments `state["social"]` | `ENABLE_SOCIAL=0` opt-in; needs `REDDIT_CLIENT_ID` + `REDDIT_CLIENT_SECRET` |

## Skipped from research-assistant's Tier 4

Explicitly **don't** transfer to structured-data monitoring:

- **HyDE** — no semantic retrieval step to rewrite queries for.
- **FLARE active retrieval** — no token-level generation we can re-retrieve on.
- **Evidence compression** — news feeds stay small at beginner scale; revisit if social context balloons.
- **Plan refinement** — pipeline is rule-driven, not plan-driven.
- **Question classifier router** — every run is a watchlist scan; no "factoid vs multihop" distinction.

See [techniques.md](techniques.md) for the reasoning with citations.

## Pipeline

```
load_config → gather (+ social?) → gather_critic → analyze → analyze_critic
                                                                    │
                                                                    ▼
                                            skeptic (self-consistency × N)
                                                                    │
                                                                    ▼
                                            verify_alerts (CoVe)
                                                                    │
                                                                    ▼
                                            alert_router → END
```

Total node count: **8** (vs beginner's 5).

## Env vars (on top of beginner's)

```bash
# Tier 4.1 / Tier 2 toggles (defaults shown)
export ENABLE_STEP_VERIFY=1
export ENABLE_VERIFY=1
export ENABLE_CONSISTENCY=1
export CONSISTENCY_SAMPLES=3

# Optional PRAW social
export ENABLE_SOCIAL=0
export REDDIT_CLIENT_ID=...
export REDDIT_CLIENT_SECRET=...
export REDDIT_USER_AGENT=agentic-ai-cookbook-lab/trading-copilot
export SOCIAL_SUBREDDITS=wallstreetbets,stocks

# Model routing (reuses research-assistant's contract)
export MODEL_PLANNER=gemma4:e2b         # analyst + critic
export MODEL_SYNTHESIZER=gemma4:e2b     # skeptic
export MODEL_VERIFIER=gemma4:e2b        # alert-claim verifier
export MODEL_CRITIC=gemma4:e2b          # step critic
```

## Run

```bash
make install     # includes PRAW even if you don't enable social; lazy-imported anyway
make smoke       # prints alerts to stdout (webhook envs unset)
make test        # 15/15 mocked tests — no network, no API keys
```

## Expected latency / cost

| Path | Extra calls vs beginner | Added latency |
|---|---|---|
| clean first pass (no critic feedback, all claims supported) | +2 critic + +(N−1)·skeptic + +1 verify per alert | +15–45s |
| one critic flagged redo | same + critic's feedback captured in notes | +5–15s |
| `ENABLE_SOCIAL=1` with PRAW configured | +1 per-ticker PRAW pull at `gather` | +2–5s per ticker |

All free on a self-hosted stack. $0 per scan.

## Observability

Every run exposes:
- `result["critic_notes"]` — feedback from step critics (gather + analyze)
- `result["alerts"][i]["vote_detail"]` — `{n: samples, kept: votes}` per alert
- `result["verified_alerts"][i]["verified_claims"]` — per-claim support decisions

Inspect these to debug why alerts are (or aren't) passing through.

## See also

- [`../beginner/`](../beginner/) — the lean base pipeline (~245 LOC)
- [`../eval/`](../eval/) — backtest harness (precision/recall over historical windows)
- [`runbook.md`](runbook.md) — symptom-cause-fix for production-tier failures
