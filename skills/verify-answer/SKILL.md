---
name: verify-answer
description: Stress-test any answer against its evidence. Extracts every factual claim, checks each against the provided sources, and marks claims as VERIFIED / UNVERIFIED / CONTRADICTED. Use before trusting a research answer, summary, or analysis — especially on multi-hop topics where one bad link corrupts the whole argument.
triggers:
  - verify this
  - fact check
  - is this accurate
  - check the claims
  - is this supported by the sources
license: MIT
author: TheAiSingularity
version: 1.0.0
---

# verify-answer

Decomposes an answer into atomic factual claims and checks each against
the evidence the user provides. Returns a clean per-claim report so the
user can see exactly what the answer got right, what it got wrong, and
what the sources didn't cover.

This skill is **prompt-only** — no tools, no network, no MCP server
required. It works in any Claude installation. Built on the
Chain-of-Verification pattern (Dhuliawala et al., 2023).

> **Looking for the automated version?** The full
> [`agentic-research-engine-oss`](https://github.com/TheAiSingularity/agentic-research-engine-oss)
> pipeline runs this verification step automatically after every
> synthesized answer, sources included. Install with
> `pip install agentic-research-engine` or
> `/plugin marketplace add https://github.com/TheAiSingularity/agentic-research-engine-oss`.

---

## How to use

Paste an answer and the sources it cites, then invoke:

```
/verify-answer
```

Or ask in plain English: *"verify this,"* *"fact-check these claims,"*
or *"is this supported by the sources?"*

**What I need from you:**

1. **The answer** — the paragraph, bullet list, or report you want verified.
2. **The evidence** — the sources it was based on. One of these forms:
   - Copy-pasted text from the sources, OR
   - URLs (I'll note which claims reference which URL but can't fetch them if I don't have browsing), OR
   - A structured list like `[1] <source text>`, `[2] <source text>`.

If you only paste the answer without evidence, I'll ask what sources you want it checked against.

---

## How I verify

For every answer, I run this protocol:

1. **Decompose** — I extract each standalone factual claim as one line.
   A claim is something like *"Paxlovid reduced hospitalization by 44 %"* — a specific, checkable statement. I **ignore** editorial hedging, conclusions, and meta-sentences.
2. **Check** — For each claim, I look through the evidence and mark it:
   - `VERIFIED` — the claim is directly supported by the evidence.
   - `UNVERIFIED` — the evidence doesn't mention this claim (not wrong, just unsupported).
   - `CONTRADICTED` — the evidence explicitly says something different from the claim.
3. **Report** — Each claim on its own line with its verdict and a one-sentence justification referencing the evidence number.
4. **Summary** — `X/Y claims verified` + the ratio + any red flags.

**Rules I follow:**
- I never invent evidence.
- If the evidence is ambiguous, I mark `UNVERIFIED` and explain what's missing.
- If the answer hedges ("may," "could," "some studies"), I preserve that hedge in the claim and check only the underlying factual part.
- I distinguish surface-level verification (the claim *appears* in the evidence) from substantive verification (the evidence *supports* the claim in context).

---

## Output format

```
── verified claims ──
✓ [claim 1]
    — supported by [2]: "<brief quote>"
✓ [claim 3]
    — supported by [1]: "<brief quote>"

── unverified claims ──
✗ [claim 2]
    — not mentioned in evidence (closest hit: [1] discusses adjacent
      topic X but not the specific assertion)

── contradicted claims ──
⚠ [claim 4]
    — evidence [3] states the opposite: "<brief quote>"

── summary ──
2/4 verified · 1 unverified · 1 contradicted
Overall: HIGH RISK — 25 % of claims contradict the evidence; do not
rely on this answer without further checking.
```

---

## Example

**User invocation:**
```
/verify-answer

Answer: Paxlovid reduced COVID-19 hospitalization in vaccinated adults
by 44 %, compared to molnupiravir which reduced it by only 8 % in the
same cohort. Both drugs work by inhibiting viral protease.

Evidence:
[1] NEJM 2023 cohort: Paxlovid reduced hospitalization 44 % relative
    to placebo in vaccinated high-risk adults.
[2] PANORAMIC trial: molnupiravir did not show statistically
    significant hospitalization reduction among vaccinated adults,
    p = 0.42.
[3] FDA: Paxlovid (nirmatrelvir) is a protease inhibitor.
```

**My output:**
```
── verified claims ──
✓ Paxlovid reduced COVID-19 hospitalization by 44 % in vaccinated adults
    — supported by [1]
✓ Paxlovid works by inhibiting viral protease
    — supported by [3]

── unverified claims ──
✗ Molnupiravir works by inhibiting viral protease
    — evidence does not describe molnupiravir's mechanism

── contradicted claims ──
⚠ Molnupiravir reduced hospitalization by 8 % in the same cohort
    — evidence [2] says PANORAMIC found NO statistically significant
      reduction for molnupiravir in vaccinated adults; the "8 %" figure
      is not in the evidence and contradicts the trial's null result.

── summary ──
2/4 verified · 1 unverified · 1 contradicted
Overall: HIGH RISK — the molnupiravir efficacy number is either a
fabrication or from a source not provided. Re-check.
```

---

## When NOT to use me

- **Creative writing / opinion / editorial pieces** — I'm a factual verifier, not a taste critic.
- **When you haven't provided evidence** — without sources, I can only guess; I'll ask you to paste them first.
- **For numerical calculation** — I check that a number appears in the evidence, not that the math is right. Use a calculator for arithmetic.
- **For live-web fact-checking** — I don't fetch URLs. If you only paste links, I'll tell you what I can't verify.

---

## Why this skill exists

Modern LLM answers are fluent enough to blur the line between
well-sourced claims and fabrications. The Chain-of-Verification pattern
(Dhuliawala et al., 2023) showed that **decomposing an answer into
claims and checking each independently against sources cuts
hallucination significantly** — this skill packages that discipline
into a one-command flow.

If you find yourself running `/verify-answer` often, the full
[`agentic-research-engine-oss`](https://github.com/TheAiSingularity/agentic-research-engine-oss)
bakes this verification into every single research query it runs.

---

## Related

- 🔗 [Full agentic-research-engine-oss](https://github.com/TheAiSingularity/agentic-research-engine-oss) — research agent that runs this verification automatically on every answer, with CLI / TUI / Web GUI / MCP server
- 📄 [Chain-of-Verification paper (Dhuliawala et al., 2023)](https://arxiv.org/abs/2309.11495)
- 🛠️ `pip install agentic-research-engine` or install the Claude plugin via `/plugin marketplace add https://github.com/TheAiSingularity/agentic-research-engine-oss`
