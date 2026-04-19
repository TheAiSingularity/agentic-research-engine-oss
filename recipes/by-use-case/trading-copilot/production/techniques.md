# Techniques — trading-copilot/production

The techniques layered on top of the beginner tier, with primary-source
citations. Reuses all the beginner stack (yfinance / `ta` / SearXNG news
/ webhook adapters) — see [`../beginner/techniques.md`](../beginner/techniques.md)
for those.

---

## T4.1 · Step-level critic (ThinkPRM pattern)

**Why:** Adapts the ThinkPRM / process-reward-model idea from reasoning
research to agent pipelines. A cheap LLM judges each major step's output
with a structured `VERDICT: accept | redo` + `FEEDBACK:` protocol. For
our domain:
- **gather critic** — did we actually cover each ticker with prices + news?
- **analyze critic** — do candidates cite specific rule fires and data points?

Fail-soft: feedback is recorded in `state["critic_notes"]` for
observability but doesn't hard-fail the pipeline. Keeps the graph simple
and makes debugging live runs much easier.

- [ThinkPRM — Process Reward Models That Think (arXiv 2504.16828)](https://arxiv.org/pdf/2504.16828)
- [Scaling Automated Process Verifiers for LLM Reasoning (arXiv 2410.08146)](https://arxiv.org/pdf/2410.08146)

## T2 · Self-consistency skeptic (adaptive N)

**Why:** The skeptic is the most important decision in the pipeline
— false positives here mean noisy alerts downstream. A majority vote
across N skeptic samples catches the cases where a single sample
rationalizes a bad candidate.

**Why adaptive:** Full N=3 voting on every candidate is wasteful when
the signal is unambiguous (high severity + short concrete reasoning).
We set N=1 for clear cases and N=`CONSISTENCY_SAMPLES` (default 3) for
borderline ones. Same compute-optimal pattern as
research-assistant's classifier router, but applied at a per-candidate
level instead of per-query.

- [Self-Consistency Improves Chain-of-Thought (Wang et al. 2022)](https://arxiv.org/abs/2203.11171)
- [Multiagent Debate Improves Reasoning and Factual Accuracy](https://composable-models.github.io/llm_debate/)
  — gains often matched at lower compute by majority voting alone.

## T2 · CoVe-style alert verification

**Why:** Direct trading-domain analog of research-assistant's
Chain-of-Verification. Instead of verifying claims in a research answer
against evidence, we verify claims in the alert's *reasoning* against
the raw numerical snapshot + news headlines. When the analyst writes
"RSI below 30 and earnings beat", we check both claims independently:
- "RSI below 30" → `state["prices"][ticker]["rsi14"] < 30`
- "earnings beat" → is there a news headline that says so?

Unsupported claim → drop the alert. Same architectural lever
MiroThinker-H1 uses (+14 points on BrowseComp); different data source.

- [Chain-of-Verification (Dhuliawala et al. 2023)](https://arxiv.org/abs/2309.11495)
- [MiroThinker-H1](https://github.com/MiroMindAI/MiroThinker) — verification-integrated agent reasoning.

## Optional · Social layer (PRAW for Reddit)

**Why opt-in:** Social sentiment is famously noisy on retail forums
(r/wallstreetbets, r/stocks). For some edge cases it's a useful
complement to news — e.g., unusual mention volume can signal something
brewing that mainstream news hasn't caught yet. But PRAW requires a
free OAuth credential, which pushes it out of zero-config territory.

**Why PRAW not X/Twitter:** X's free tier is effectively shut in 2026
(1 req per 15 min); paid Basic tier is $100/mo. Reddit still ships a
usable free API via PRAW.

- [PRAW documentation](https://praw.readthedocs.io/)
- [Twitter/X API pricing 2026 — why we skip it](https://www.xpoz.ai/blog/guides/understanding-twitter-api-pricing-tiers-and-alternatives/)

## Techniques we deliberately DON'T port from research-assistant

- **HyDE** — we don't have a semantic-retrieval step for HyDE to augment.
- **FLARE active retrieval** — no token-level generation stream to hook
  into; our synthesis is structured fields from the skeptic.
- **Evidence compression** — news per ticker is already small (≤5 headlines);
  beginner scale doesn't need it. If `ENABLE_SOCIAL=1` produces very
  chatty feeds, revisit.
- **Plan refinement / classifier router** — pipeline is rule-driven, not
  plan-driven; every scan classifies identically as "watchlist pass".

## What nobody tells you

**The CoVe verify step is where most LLM hallucinations actually get
caught — not the skeptic.** A small open-weight model (gemma4:e2b,
2B effective) can rationalize a bad candidate through the skeptic role
if given a plausibly-worded trigger. But when you then ask it "here's
the raw snapshot; does each claim in the alert hold?", the contradiction
surfaces more reliably because it's checking numeric facts, not
directional judgements. Cheap, deterministic, very effective.
