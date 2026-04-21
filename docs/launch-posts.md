# Launch posts — v0.1.3

All copy is ready to ship. Core narrative across every platform:

> *"I built a local research agent. I ran real benchmarks. 0/20 on
> SimpleQA-mini. Here's what that actually means — and why switching
> to GPT-5 doesn't fix it."*

Each post has a different wrapper for a different audience but keeps
the same honest-benchmark hook.

## Recommended shipping order (one day)

| time (PT) | channel | why |
|---|---|---|
| 06:00 | **Show HN** | HN prime-time window opens ~6–9am PT |
| 06:05 | **X thread** | cross-link from HN comments to thread; mutually amplifying |
| 09:00 | **r/LocalLLaMA** | US morning / EU afternoon peak |
| 11:00 | **LinkedIn** | LinkedIn engagement window |
| 13:00 | **r/MachineLearning** | afternoon reddit peak |
| 16:00 | **Medium** + **Dev.to** | evergreen anchor, link from all above |
| 18:00 | **GitHub Discussions** | closes the loop for existing stargazers |

Don't ship multiple Reddit subs at once — the mod bots notice and
can shadow-ban. Stagger by 2+ hours.

---

## 1 · Show HN

### Title

```
Show HN: Agentic Research – local research agent that verifies its own answers
```

### Body

```
Three weeks of building this on Gemma 3 4B (Ollama) + SearXNG
+ trafilatura + a Chain-of-Verification loop. Laptop-local,
$0/query, MIT, no telemetry. 137 mocked tests, zero-network.

The part I want feedback on is the benchmark post-mortem.

On a 20-question SimpleQA-mini fixture I wrote, Gemma 3 4B
passed 0/20 on strict substring scoring — but verified_ratio
was 85.5% (65/76 claims backed by retrieved evidence). The
pattern: when SearXNG didn't return a source with the gold
token, Gemma confidently picked a wrong token from its
pre-training memory. Example: "What year did Anthropic publish
Contextual Retrieval?" → "2023" (gold: 2024).

On a broader 10-question BrowseComp-mini (multi-hop synthesis,
not substring recall), the same engine passed 4/10 with 100%
per-claim faithfulness. So the 0/20 is a specific failure mode,
not a blanket result.

Ran the 5 hardest SimpleQA failures on gpt-5-nano + gpt-5-mini
cloud, expecting a big lift. Got 1/5. But on 4/5 the cloud
model refused to confabulate ("evidence does not answer") where
Gemma had guessed. Per-claim faithfulness 82.9% → 100%.

Cloud doesn't make the pipeline smarter. It makes it honest.
The bottleneck is retrieval, not synthesis.

Per-question diffs + methodology:
https://github.com/TheAiSingularity/agentic-research-engine-oss/blob/main/engine/benchmarks/RESULTS.md

Pipeline: 8-node LangGraph (classify → plan → search → retrieve
→ fetch → compress → synthesize → verify), every node env-toggleable
for ablation. HyDE, FLARE active retrieval, hybrid BM25+dense+RRF,
cross-encoder rerank (bge-reranker-v2-m3, opt-in), contextual
chunking, LongLLMLingua-lite compression, ThinkPRM critic.

Ships as CLI / TUI / Web GUI / MCP server. On PyPI +
registry.modelcontextprotocol.io + the Anthropic plugin
marketplace.

Repo: https://github.com/TheAiSingularity/agentic-research-engine-oss

Would especially welcome feedback on:
- Standard RAG benchmarks worth running next (BEIR? NoMIRACL?
  public BrowseComp subsets?)
- Whether LLM-as-judge scoring leaks signal when the judge and
  synthesizer share a family
- How MCP-agent builders evaluate multi-node pipelines end-to-end
```

### First comment (post immediately after submission)

```
Author here. Quick install for anyone who wants to try before reading:

  brew install ollama
  ollama pull gemma3:4b nomic-embed-text
  docker run -d -p 8888:8080 searxng/searxng
  pip install agentic-research-engine
  agentic-research ask "what is Anthropic's contextual retrieval?" --domain papers

~45s for a factoid, ~90s for multi-hop. Zero dollars.

Or drop it into Claude Desktop / Cursor via:

  /plugin marketplace add https://github.com/TheAiSingularity/agentic-research-engine-oss
  /plugin install agentic-research

The honest-benchmark writeup is the more interesting read, though.
```

---

## 2 · r/LocalLLaMA

### Title

```
[Open-source] Local research agent on Gemma 3 4B + Ollama — $0/query, ships as MCP + CLI + TUI + Web GUI, benchmarks published
```

### Body

```
Spent three weeks on this. Open-source end-to-end (MIT), no
telemetry, no cloud dependency by default.

Stack:
- Gemma 3 4B via Ollama (3.3 GB on disk)
- nomic-embed-text via Ollama (270 MB)
- SearXNG self-hosted (Docker, one-liner)
- trafilatura for full-page extraction
- Hybrid BM25 + dense + RRF retrieval
- Optional cross-encoder rerank via bge-reranker-v2-m3 (560 MB, opt-in)
- 8-node LangGraph pipeline with Chain-of-Verification
- ~45s per factoid, ~90s multi-hop on M-series Mac

Benchmarks (measured 2026-04-21, full data + per-question diffs
in the repo):
- SimpleQA-mini 20 Q: 0/20 strict pass, 85.5% verified per-claim, 41.3s mean
- BrowseComp-mini 10 Q: 4/10 pass, 100% verified per-claim, 33.1s mean

The 0/20 is honest, not a fail. gemma3:4b confabulates specific
factoid tokens ("2023" vs gold "2024") when SearXNG doesn't surface
the right source. Not fabricating claims — picking wrong tokens from
pre-training memory. Per-claim faithfulness stayed at 85.5%.

Also benchmarked the full cloud stack (gpt-5-nano + gpt-5-mini) on
the 5 hardest failures. Only 1 flipped to pass. But on the other 4,
the cloud model refused to confabulate entirely ("evidence does not
answer"). Cloud makes it more honest, not smarter. Retrieval is the
real bottleneck.

Four interfaces, pick one:
- CLI: `pip install agentic-research-engine && agentic-research ask "..."`
- TUI: Textual 3-pane (sources / answer / trace), SSH-safe
- Web GUI: FastAPI + HTMX, localhost:8080, streams tokens
- MCP server: /plugin marketplace add (...) in Claude Desktop / Cursor / Continue

Works with any OpenAI-compatible endpoint — Groq, Together, vLLM,
llama.cpp server, SGLang. One env var (OPENAI_BASE_URL).

Six domain presets (general, medical, papers, financial, stock_trading,
personal_docs) — each is ~10-line YAML; write your own in ten minutes.

Point LOCAL_CORPUS_PATH at an indexed corpus of your own docs and
retrieval hits them alongside web search.

Every pipeline node is env-toggleable for ablation studies:
`ENABLE_RERANK`, `ENABLE_FETCH`, `ENABLE_COMPRESS`, `ENABLE_VERIFY`,
`ENABLE_ACTIVE_RETR`, `ENABLE_ROUTER`.

137 mocked tests, all zero-network. MIT.

GitHub: https://github.com/TheAiSingularity/agentic-research-engine-oss
PyPI: https://pypi.org/project/agentic-research-engine/
RESULTS: https://github.com/TheAiSingularity/agentic-research-engine-oss/blob/main/engine/benchmarks/RESULTS.md

Feedback welcome — especially on better fixtures, ablation suggestions,
and if anyone's running a 7B-13B local model with higher factoid
recall, I'd love to compare.
```

---

## 3 · r/MachineLearning

### Title

```
[P] Open-source local research agent + honest benchmark — what a 0/20 SimpleQA pass-rate actually means (and why GPT-5 doesn't fix it)
```

### Body

```
Shipping v0.1.3 of an open-source (MIT) research agent on Gemma 3 4B
+ SearXNG + trafilatura + Chain-of-Verification. Runs on a laptop
for $0/query. Code: https://github.com/TheAiSingularity/agentic-research-engine-oss

Posting here (rather than /r/programming) because I want to discuss
the benchmark methodology.

**Setup:**
- 20-question SimpleQA-mini fixture (self-written, factoid recall,
  self-referential to the engine's own stack)
- Strict substring scoring against must_contain / must_not_contain lists
- Shipping defaults: ENABLE_RERANK=0, ENABLE_FETCH=1, CoVe on, 2-iter cap

**Result:**
- pass rate: 0/20 (0.0%)
- verified_ratio: 65/76 (85.5%)
- mean wall: 41.3 s
- must_not_contain hits: 0

**Three failure modes:**

1. *Confident factoid hallucination (~7/20).* When SearXNG didn't
   return a source with the gold token, the 4B model picked wrong
   tokens from its pre-training prior. Example: "What year did
   Anthropic publish Contextual Retrieval?" → "2023" (gold: 2024).

2. *CoVe verifies wrong answers.* verified_ratio was 85.5%, which
   looks healthy. But CoVe only checks the synthesizer's claims
   against the retrieved evidence pool — not against ground truth.
   On the "2023" answer, 5/5 claims CoVe-verified. Still wrong. I
   think the literature doesn't emphasize this limitation enough.

3. *Self-referential fixture design was a mistake.* I assumed
   SearXNG would surface our repo for queries about our own stack.
   It doesn't reliably. Honest abstentions from the model
   ("the evidence does not answer this question") got scored as
   misses.

**Cloud comparison:**

Ran the 5 hardest failures through gpt-5-nano + gpt-5-mini cloud
(same retrieval pipeline, swap only the synthesizer + planner):

```
model                      pass    verified      mean wall
gemma3:4b (local)          0 / 5   29/35  82.9%  52 s   $0/q
gpt-5-nano+gpt-5-mini      1 / 5   52/52 100.0%  127 s  ~$0.02/q
```

Pass rate barely moved. Per-claim faithfulness flipped to 100%.
The cloud model refused to confabulate on 4/5 questions where Gemma
had guessed. Takeaway: bigger models make the pipeline more honest,
not smarter. Retrieval is the bottleneck.

**Questions for /r/ML:**
- What RAG fixtures do you consider gold-standard for open
  benchmarking? BEIR? NoMIRACL? Are there public BrowseComp
  subsets?
- Does LLM-as-judge scoring leak signal when the judge and
  synthesizer come from the same model family?
- Retrieval evaluation independent of generation — feels like
  the community conflates the two. Is anyone working on it?

Full results + per-question diffs:
https://github.com/TheAiSingularity/agentic-research-engine-oss/blob/main/engine/benchmarks/RESULTS.md

Paper-adjacent techniques in the pipeline: HyDE (Gao et al 2023),
FLARE (Jiang et al 2023), CoVe (Dhuliawala et al 2023), RRF
(Cormack 2009), Contextual Retrieval (Anthropic 2024),
bge-reranker-v2-m3 (BAAI 2024), LongLLMLingua-lite (Jiang et al
2023), ThinkPRM-pattern step critic.

137 mocked tests, zero-network. MIT.
```

---

## 4 · X / Twitter thread

8 tweets, all ≤ 280 chars. Each one standalone enough to quote-tweet.

### Tweet 1 (hook)

```
I spent 3 weeks building a local research agent.

Runs on Gemma 3 4B + Ollama on a laptop for $0/query.

Then I benchmarked it honestly.

0/20 on my own SimpleQA fixture.

Here's what that actually means (and why swapping to GPT-5 doesn't fix it). 🧵
```

### Tweet 2 (what it is)

```
What it is:

Open-source (MIT) research agent. CLI + TUI + Web GUI + MCP server.

Gemma 3 4B via Ollama. SearXNG for search. trafilatura for fetch. Chain-of-Verification for hallucination defense. No telemetry.

github.com/TheAiSingularity/agentic-research-engine-oss
```

### Tweet 3 (the 0/20, explained)

```
0/20 isn't what it looks like.

verified_ratio: 85.5% — the synthesizer wasn't fabricating claims. It was picking wrong ones when retrieval missed.

e.g. "Year Anthropic published Contextual Retrieval?"
  Model: "2023"
  Gold: 2024

Confident hallucination from pre-training.
```

### Tweet 4 (cloud comparison)

```
Obvious follow-up: does gpt-5-mini fix it?

Ran the 5 hardest failures on gpt-5-nano + gpt-5-mini cloud.

Pass rate: 1/5. Tiny jump.

But per-claim faithfulness went 82.9% → 100%.

On 4/5 questions the cloud model refused to confabulate: "evidence does not answer."
```

### Tweet 5 (the punchline)

```
Cloud doesn't make the pipeline smarter.

It makes it HONEST.

The bottleneck isn't synthesis — it's retrieval. If SearXNG doesn't return a source with the gold token, neither model produces it.

Only one admits it.
```

### Tweet 6 (the lever)

```
Real accuracy lever = retrieval, not model size:

- LOCAL_CORPUS_PATH with indexed docs
- ENABLE_RERANK=1 (bge-reranker-v2-m3)
- A domain preset biased toward high-quality sources

Small local model + good retrieval > frontier cloud model + bad retrieval.
```

### Tweet 7 (what ships)

```
What ships:

✓ 8-node LangGraph, every node env-toggleable
✓ 6 domain presets (medical, papers, trading, etc)
✓ HyDE + FLARE + CoVe + hybrid BM25/dense
✓ 137 mocked tests, zero-network
✓ MIT end-to-end
```

### Tweet 8 (CTA + close)

```
Full benchmark + per-question diffs:
github.com/TheAiSingularity/agentic-research-engine-oss/blob/main/engine/benchmarks/RESULTS.md

Feedback, PRs, fixture ideas welcome.

/end
```

---

## 5 · LinkedIn

Tight, professional, lessons-focused.

```
Three weeks ago I set out to build a local research agent. Two weeks ago I shipped v0.1. Yesterday I ran real benchmarks and published the failure modes.

0 out of 20 on my own SimpleQA fixture.

I published it anyway.

The engine (agentic-research-engine-oss, open-source MIT) runs on Gemma 3 4B via Ollama, searches via SearXNG, and verifies its own claims via Chain-of-Verification. Laptop-local, $0/query.

The 0/20 isn't as bad as it looks. The verified_ratio was 85.5% — the synthesizer wasn't fabricating claims. It was picking wrong tokens from pre-training memory when retrieval missed. On the broader BrowseComp-mini (10 multi-hop questions), the same engine passed 4/10 with 100% per-claim faithfulness.

Then I ran the 5 hardest factoid failures through GPT-5-mini cloud, expecting a lift. Got 1/5. But on the other 4, the cloud model refused to confabulate — answered "the provided evidence does not answer this question" where Gemma had guessed.

Per-claim faithfulness: 82.9% → 100%.

Cloud models don't make this pipeline smarter. They make it more honest. The bottleneck is retrieval, not synthesis.

Three lessons I'll carry forward:

1. Publish your failure modes. A detailed 0/20 is more useful to users than a handwaved 70%. Users want to know where the pipeline breaks.

2. "Verified by our judge" means less than you think. Watch the gap between verified-ratio and true-positive rate. If they're equal, you haven't tested edge cases.

3. Improve retrieval before you upgrade the model. A well-indexed local corpus moves pass rate more than a 10x more expensive synthesizer — at $0.

Code (MIT) + full benchmark data:
https://github.com/TheAiSingularity/agentic-research-engine-oss

#OpenSource #AIAgents #RAG #LLM #LocalFirst
```

---

## 6 · Medium

Long-form anchor. All short posts can link back here.

### Title

```
Why my research agent scored 0/20 on its own benchmark
```

### Subtitle (Medium supports this as a separate field)

```
And why swapping to GPT-5 barely moved the needle.
```

### Body

```
Three weeks ago I set out to answer two questions:

1. Can a 4-billion-parameter local model run a real research pipeline
   on a laptop for $0 per query?
2. Can that pipeline be honest about its own failure modes?

The result is [agentic-research-engine-oss](https://github.com/TheAiSingularity/agentic-research-engine-oss)
— an open-source (MIT) research agent that runs on Gemma 3 4B via
Ollama, searches via SearXNG, fetches pages via trafilatura, and
verifies its own claims via Chain-of-Verification (CoVe). It ships
as a CLI, a Textual TUI, a FastAPI web GUI, and an MCP server you
can drop into Claude Desktop, Cursor, or Continue.

Answer to question 1: yes. The thing works. A factoid query returns
in ~45 seconds on an M-series Mac. You pay zero dollars per query.

Answer to question 2 is the part I want to write about.

## The setup

The engine ships with a 20-question SimpleQA-mini fixture — short
factoid questions about the engine's own technology stack ("What
year did Anthropic publish the Contextual Retrieval blog post?",
"What cross-encoder model does this cookbook use for reranking?").
Gold answers are single-token substrings. Scoring is strict: the
answer must contain the gold token, period.

It's a self-referential fixture by design. I wanted the engine to
be able to answer questions about its own architecture.

## The result

On 2026-04-21 I ran the full SimpleQA-mini against the shipping
defaults: Gemma 3 4B via Ollama, SearXNG, trafilatura, CoVe loop,
cross-encoder rerank off.

    passed 0/20 (0.0%)
    mean wall 41.3s
    verified 65/76 (85.5%)

Zero out of twenty. On the engine's own benchmark.

Before I explain why this is less bad than it looks, let me sit
with it for a moment.

Zero out of twenty is a headline nobody wants to publish. Every
instinct says "fix the benchmark, retry, ship good numbers."

I didn't do that. Here's why.

## What the 0/20 actually means

Three failure modes, all real:

### 1. Confident factoid hallucination (~7/20)

When SearXNG didn't return a source containing the gold token,
Gemma 3 4B happily picked a wrong token from its pre-training
memory. Examples:

- *What year did Anthropic publish the Contextual Retrieval blog
  post?* → Gemma: "2023" (gold: 2024).
- *Which cross-encoder model does this cookbook use for reranking?*
  → Gemma: "LayoutLMv3 Cross-Encoder" (gold: bge-reranker-v2-m3).
- *Which meta-search engine does this cookbook self-host?* → Gemma:
  "Google Cookbook is a feature within Google that allows users to
  discover, save, and organize recipes..." (gold: SearXNG).

The last one is comedic. The model latched onto "Google Cookbook"
recipe-site results from web search and synthesized nonsense. But
it's the same failure pattern: when retrieval fails, the model
doesn't abstain; it invents.

### 2. CoVe verifies wrong answers (85.5% verified ratio)

The Chain-of-Verification loop decomposes the answer into claims
and checks each claim against retrieved evidence. On SimpleQA,
that loop verified 65/76 claims — 85.5%.

But *verified against retrieved evidence* ≠ *verified against
ground truth.* On the "2023" answer above, 5 of 5 claims
CoVe-verified. The answer was still wrong. CoVe caught unsupported
extrapolation; it couldn't catch wrong-but-cited.

This is not a CoVe bug. CoVe is doing exactly what it's designed
to do — confirm the synthesizer didn't invent facts absent from the
evidence pool. The failure was upstream: wrong evidence entered
the pool, the model trusted it, CoVe trusted the model.

### 3. Self-referential fixture design (~8/20)

The fixture asks questions whose answers live in the engine's own
GitHub repo. I assumed SearXNG would surface the repo. It often
doesn't. When the retrieval pool doesn't contain the right token,
the model either abstains (honest, but fails `must_contain`) or
hallucinates (also fails, but for a different reason).

Sample honest-abstention:

- *Which LangGraph node runs between fetch_url and synthesize?*
- Gemma: "The provided evidence does not answer this question."
- Gold: `compress`.

The model was right to abstain. The benchmark was wrong to assume
retrieval would find the answer.

## Why I didn't fix the benchmark before publishing

My first instinct was "rewrite the fixture, retry, ship 70%+." That
would have been easy. SimpleQA-mini could trivially be rewritten
with questions whose answers are widely indexed on the open web.

But the 0/20 is more useful than the fixed fixture would be.

It makes three things legible that are otherwise invisible:

1. **Verified-ratio is not accuracy.** Teams often proxy quality
   with verification-pass rates from their own LLM-judge setups.
   My pipeline's CoVe loop reported 85.5% verified, and the pass
   rate was 0%. Anyone who trusts that proxy deserves to know the
   gap.
2. **Small-model factoid confabulation is a real phenomenon,
   quantified.** Not a vibe — 7 of 20 cases on a specific fixture,
   with per-question diffs.
3. **The fixture's self-referential design was a mistake.** I
   documented it so the next contributor doesn't make it.

## What about cloud models?

The obvious next question: does swapping to a frontier cloud model
fix this? I ran the 5 hardest factoid failures through gpt-5-nano
+ gpt-5-mini (via OpenAI). Same retrieval pipeline, different
synthesizer.

    model                      pass    verified      mean wall
    gemma3:4b (local)          0 / 5   29/35  82.9%  52 s
    gpt-5-nano+gpt-5-mini      1 / 5   52/52 100.0%  127 s (~$0.02/q)

One pass flipped: *sqa-01* (Anthropic CR year) went from "2023" to
"2024". The cloud model trusted the retrieved evidence over its own
prior.

On the other four: the cloud model refused to confabulate. *"The
provided evidence does not answer this question."*

Per-claim faithfulness went from 82.9% → 100%. The cloud model
strictly obeyed the evidence constraint. Gemma hadn't.

The takeaway isn't what I expected going in. Cloud models don't
make the pipeline smarter. They make it more honest. On 4/5
questions, gpt-5-mini correctly abstained where Gemma had guessed.
Same retrieval, different obedience.

The bottleneck isn't synthesis. It's retrieval. If SearXNG doesn't
return a source containing the gold token, neither model produces
it. Only one admits it.

## Where the engine does well

Before anyone concludes the whole thing doesn't work: on
BrowseComp-mini (10 broader, multi-hop synthesis questions), the
same engine on the same Gemma 3 4B passed 4/10 with 100% per-claim
faithfulness. Those questions don't have single-token gold answers
— they're scored on whether the synthesized answer covers the
expected concepts. That's where an 8-node pipeline with CoVe earns
its keep.

SimpleQA probes a specific weakness: factoid recall on tokens the
search index may not surface. It's a real weakness, worth measuring,
worth sharing.

## What this means if you're building RAG

Three takeaways:

1. **Publish your failure modes.** A 0/20 that's explained in detail
   is more useful than a 70% that handwaves. Your users want to
   know where the pipeline breaks, not where it shines.
2. **"Verified by our judge" means less than you think.** Watch the
   gap between verified-ratio and true-positive rate. If they're
   equal, you haven't probed the cases where retrieval fails.
3. **Improve retrieval before you upgrade the model.** On this
   pipeline, swapping gemma3:4b → gpt-5-mini costs ~$0.02/query
   and moves pass rate by 20 percentage points (1 question in 5).
   Adding a well-indexed local corpus would almost certainly move
   it more — at $0.

## If you want to try it

30-second install:

    brew install ollama
    ollama pull gemma3:4b nomic-embed-text
    docker run -d -p 8888:8080 searxng/searxng
    pip install agentic-research-engine

    agentic-research ask "what is Anthropic's contextual retrieval?" --domain papers

Or drop it into Claude Desktop / Cursor / Continue:

    /plugin marketplace add https://github.com/TheAiSingularity/agentic-research-engine-oss
    /plugin install agentic-research

- [Repo](https://github.com/TheAiSingularity/agentic-research-engine-oss)
- [Full benchmark data + per-question diffs](https://github.com/TheAiSingularity/agentic-research-engine-oss/blob/main/engine/benchmarks/RESULTS.md)
- [PyPI](https://pypi.org/project/agentic-research-engine/)
- [Official MCP registry entry](https://registry.modelcontextprotocol.io/v0/servers?search=agentic-research)

137 mocked tests. MIT. No telemetry. Runs on a laptop.

Feedback welcome — especially on better fixtures to run, whether
LLM-as-judge scoring leaks signal, and how other MCP-agent builders
evaluate multi-node pipelines.
```

### Tags

`artificial-intelligence`, `llm`, `open-source`, `rag`, `retrieval-augmented-generation`, `ollama`, `local-first`

---

## 7 · Dev.to

Developer-focused, code-heavy, markdown-native.

### Title

```
I built a local research agent that verifies its own answers — and published why it fails
```

### Body

````markdown
Spent three weeks building [agentic-research-engine-oss](https://github.com/TheAiSingularity/agentic-research-engine-oss)
— a local-first research agent on Gemma 3 4B (via Ollama), SearXNG,
trafilatura, and a Chain-of-Verification loop.

Ships as a CLI, a Textual TUI, a FastAPI web GUI, and an MCP server.
MIT, no telemetry, runs on a laptop for $0 per query.

Here's what makes it interesting — and what doesn't.

## The 30-second install

```bash
brew install ollama
ollama pull gemma3:4b nomic-embed-text
docker run -d -p 8888:8080 searxng/searxng
pip install agentic-research-engine

agentic-research ask "what is Anthropic's contextual retrieval?" --domain papers
```

First query takes ~60s (model warmup); subsequent queries run ~45s
on an M-series Mac.

## The 8-node pipeline

```
classify → plan → search → retrieve → fetch_url → compress → synthesize → verify
```

Every node is env-toggleable for ablation:

```bash
ENABLE_FETCH=0         # skip trafilatura full-page fetch
ENABLE_COMPRESS=0      # skip LongLLMLingua-lite
ENABLE_VERIFY=0        # skip Chain-of-Verification
ENABLE_ACTIVE_RETR=0   # skip FLARE
ENABLE_ROUTER=0        # skip ThinkPRM critic router
ENABLE_RERANK=1        # turn on bge-reranker-v2-m3 (opt-in)
```

Techniques folded in: HyDE plan expansion, FLARE active retrieval,
CoVe verification, hybrid BM25 + dense + RRF retrieval, contextual
chunking (Anthropic pattern), LongLLMLingua-lite compression,
cross-encoder rerank, ThinkPRM-pattern critic. 137 mocked tests,
all zero-network.

## The honest benchmark

Yesterday I ran the first live benchmark on shipping defaults:

```
SimpleQA-mini (20 Q)      passed 0/20 (0.0%)   verified 65/76 (85.5%)   41.3s mean
BrowseComp-mini (10 Q)    passed 4/10 (40.0%)  verified 37/37 (100.0%)  33.1s mean
```

0/20 on a self-written fixture looks terrible. Here's what's happening.

The fixture asks factoid questions about the engine's own tech stack.
Strict substring scoring. Three failure modes:

**1. Confident hallucination when retrieval misses.**

```
Q: "What year did Anthropic publish Contextual Retrieval?"
Model: "2023 [1,2,3,4,5]"  ← wrong
Gold:  "2024"
```

SearXNG didn't return a source containing "2024". Gemma picked
"2023" from pre-training memory and confidently cited five sources.

**2. CoVe verifies wrong answers.**

A `verified_ratio` of 85.5% sounds healthy. But on that "2023"
answer, 5/5 claims CoVe-verified. The answer was still wrong.

CoVe checks the synthesizer's claims against retrieved evidence.
It doesn't check against ground truth. If wrong evidence enters
the pool, CoVe doesn't catch it.

**3. Self-referential fixture.**

I assumed SearXNG would surface the engine's own repo. It doesn't
reliably. Many questions got honest *"evidence does not answer"*
abstentions that failed the strict `must_contain` check.

## Does swapping to GPT-5 fix it?

Ran the 5 hardest failures through gpt-5-nano + gpt-5-mini cloud:

```
model                      pass    verified      mean wall
gemma3:4b (local)          0 / 5   29/35  82.9%  52 s     $0/q
gpt-5-nano+gpt-5-mini      1 / 5   52/52 100.0%  127 s    ~$0.02/q
```

Pass rate: 0 → 1. Small.

But on 4 of 5 questions, gpt-5-mini refused to confabulate: *"The
provided evidence does not answer this question."*

Per-claim faithfulness: 82.9% → 100%.

**Cloud models don't make this pipeline smarter. They make it
more honest.** The bottleneck is retrieval, not synthesis.

## What this means if you're building RAG

1. **Publish failure modes.** 0/20 that's explained is more useful
   than 70% that handwaves. Users need to know where the pipeline
   breaks.
2. **`verified_ratio` is not accuracy.** If your LLM-judge agrees
   with itself, it agrees with itself. That's all.
3. **Improve retrieval before you upgrade the model.** Swapping
   gemma3:4b → gpt-5-mini costs $0.02/query and moves pass rate
   by 20 percentage points. A well-indexed local corpus would move
   it more — at $0.

Full per-question diffs + methodology:
https://github.com/TheAiSingularity/agentic-research-engine-oss/blob/main/engine/benchmarks/RESULTS.md

## Four ways to drive it

```bash
# CLI
agentic-research ask "..." --domain papers

# TUI (Textual; 3 panes; SSH-safe)
make tui

# Web GUI (FastAPI + HTMX; localhost:8080; streams tokens; dark theme)
make gui

# MCP server — drop into Claude Desktop / Cursor / Continue:
#   /plugin marketplace add https://github.com/TheAiSingularity/agentic-research-engine-oss
```

## One env var to go cloud

```bash
unset OPENAI_BASE_URL                 # drop Ollama
export OPENAI_API_KEY=sk-...
# Defaults are already cloud-sized (gpt-5-nano + gpt-5-mini);
# explicit override if you want to pin:
export MODEL_PLANNER=gpt-5-nano
export MODEL_SYNTHESIZER=gpt-5-mini   # or claude-sonnet-4-5, llama-3.3-70b on Groq, etc.
```

Works with any OpenAI-compatible endpoint.

## Links

- [GitHub](https://github.com/TheAiSingularity/agentic-research-engine-oss)
- [PyPI](https://pypi.org/project/agentic-research-engine/)
- [MCP registry](https://registry.modelcontextprotocol.io/v0/servers?search=agentic-research)
- [Benchmark RESULTS.md](https://github.com/TheAiSingularity/agentic-research-engine-oss/blob/main/engine/benchmarks/RESULTS.md)

Feedback, PRs, fixture suggestions all welcome.
````

### Dev.to tags

`rag`, `opensource`, `ai`, `python`

---

## 8 · GitHub Discussions — v0.1.3 announcement

Post under the repo's Discussions → Announcements category.

### Title

```
v0.1.3 — on PyPI + the official MCP registry + the Claude plugin marketplace
```

### Body

```markdown
Quick update on where the project stands.

## Installable surfaces

- **PyPI** — `pip install agentic-research-engine` (v0.1.3)
- **MCP registry** — `io.github.TheAiSingularity/agentic-research`, `status=active`, `isLatest=true`
- **Anthropic plugin marketplace** — `/plugin marketplace add https://github.com/TheAiSingularity/agentic-research-engine-oss`
- **Docker / Docker Compose** — still on the 0.2 roadmap

## New in 0.1.3

- First honest live benchmark ships (SimpleQA-mini + BrowseComp-mini)
- Standalone `verify-answer` skill (`skills/verify-answer/SKILL.md`) —
  prompt-only Chain-of-Verification, no engine required
- `gpt-5` temperature-kwarg fix — engine no longer crashes when you
  swap `MODEL_SYNTHESIZER=gpt-5-mini`
- README "Higher honesty — cloud-model mode" section with a real
  side-by-side comparison (0/5 local vs 1/5 cloud; 82.9% → 100%
  per-claim faithfulness)
- Result snapshots checked into `engine/benchmarks/results/2026-04-21/`
  so future PRs have a reference point
- Submission docs under `docs/submit-*.md` (PyPI, MCP registry,
  Claude plugin marketplace, four community directories)

## What the 0/20 on SimpleQA means

Full story in `engine/benchmarks/RESULTS.md`. Short version: the
engine didn't fabricate claims (verified_ratio 85.5%) — it picked
wrong tokens when retrieval missed. Cloud models don't fix this;
they make the engine more honest, not smarter. Retrieval is the
real bottleneck.

## What's next

- [ ] LLM-as-judge scorer alongside `must_contain`
- [ ] Less self-referential SimpleQA fixture (web-indexed gold)
- [ ] Per-node base URL routing (run gemma3:4b for plan/verify and
      gpt-5-mini for synth in the same query)
- [ ] Ablation run: `--ablate no-fetch` and `--ablate no-compress`
      deltas for RESULTS.md
- [ ] Docker Compose for "one command, everything wired"
- [ ] v0.2 — specialist tool wiring (`tools_enabled` in presets),
      plugin catalog

Feedback + PRs welcome. If you have a better fixture than SimpleQA-mini
for testing factoid recall, open an issue.
```

---

## Pre-flight checklist

Before shipping any of the above, confirm:

- [ ] GitHub repo is public and the latest commit on `main` is current
- [ ] `https://pypi.org/project/agentic-research-engine/` shows 0.1.3
- [ ] `curl "https://registry.modelcontextprotocol.io/v0/servers?search=agentic-research"` returns our server with `isLatest=true`
- [ ] README.md badge shows 0.1.3-alpha
- [ ] `engine/benchmarks/RESULTS.md` renders cleanly on GitHub with
      both the SimpleQA Phase 9 + Cloud Phase 9b sections
- [ ] Claude plugin marketplace install flow works end-to-end:
      `/plugin marketplace add ... → /plugin install agentic-research → /research "..."`
- [ ] Quickstart from README copy-pasted into a fresh terminal returns
      a sensible answer
- [ ] No CLAUDE.md / other internal doc references accidentally committed

### Visuals to prep (optional but high-leverage)

X + r/LocalLLaMA + LinkedIn + Dev.to reward good visuals. Consider
attaching to at least the X thread and the Reddit post:

- **TUI screenshot** — 3-pane layout (sources / answer / trace) in
  mid-query, streaming tokens visible. Easiest flex of what the
  engine does without a video.
- **Architecture diagram** — 8-node pipeline box-and-arrow diagram
  with env toggles labeled. Can be quick whiteboard → scan.
- **Benchmark table screenshot** — the side-by-side from RESULTS.md
  Phase 9b (gemma3:4b vs gpt-5-nano+gpt-5-mini). The 82.9% → 100%
  faithfulness delta is the headline numeric.
- **Terminal recording / GIF** — `agentic-research ask "..."`
  streaming an answer in ~45s. `asciinema` + `svg-term-cli` for
  Twitter-safe SVG.

---

## After shipping

- Note which channel drove the most clickthrough in the first 24h
  (GitHub insights + star velocity will tell you).
- If any of the 4 community directories (glama.ai / mcp.so / pulsemcp /
  claudemarketplaces) hasn't indexed us by 2026-04-22 22:00 UTC,
  open the escalation issues using the templates in
  `docs/submit-community-directories.md`.
- Engage with HN / Reddit comments for the first 2-3 hours — early
  engagement is what the ranking algorithms reward.
- **Never** respond defensively to critical comments. Lead with
  agreement where there's a real point; link to the code where the
  answer is "it's in the repo." Silence is usually better than
  defensiveness.
