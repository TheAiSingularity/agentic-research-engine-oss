# Runbook — research-assistant/production

What to look at when the pipeline misbehaves.

## Symptom → likely cause → fix

### "verify reports 0/0 claims"
- **Cause:** Verifier model returned free text not matching the `CLAIM: … / VERIFIED: yes|no` protocol.
- **Fix:** Use a more instruction-following model for `MODEL_VERIFIER`. Some small open-weights (e.g. gemma4:e2b) drift on format under pressure. Try `gemma4:e4b` or the bigger Qwen3.6 variants.

### "pipeline hits MAX_ITERATIONS on every question"
- **Cause:** Verifier is being too strict, or the summarizer is hallucinating claims that never grounded in evidence.
- **Fix:** Inspect one run manually — if the answer's claims *are* supported but the verifier says "no", the verifier is the problem; switch model. If the claims aren't supported, tighten the synthesizer prompt (already explicit about "if not supported, say so").

### "answer has [7] but only 5 evidence items"
- **Cause:** Synthesizer hallucinated citation indices.
- **Fix:** `eval/scorer.py`'s `citation_accuracy` metric catches this. Production tier doesn't auto-fix it; CoVe only flags *claims*, not citation indices. Consider wrapping `_synthesize` with a pre-return sanitizer that clamps refs to valid range — add as a follow-up if this is prevalent in your eval.

### "HyDE is making retrieval worse for questions about dates / numbers"
- **Cause:** HyDE generates a plausible-sounding but factually wrong hypothetical document, which misleads the retriever.
- **Fix:** The gate in `_plan` (`_NUMERIC_RE`) already skips obvious numeric queries. If you hit edge cases, either tighten the regex or set `ENABLE_HYDE=0` for your workload.

### "Ollama stalls on the verify pass"
- **Cause:** Default Ollama context window is 2048; the verify prompt (answer + all evidence) can exceed it.
- **Fix:** Increase Ollama's context window via `OLLAMA_CONTEXT_LENGTH` env var on the Ollama daemon, or reduce `TOP_K_EVIDENCE`.

### "ENABLE_CONSISTENCY=1 makes runs 3–4× slower with tiny accuracy gains"
- **Cause:** Self-consistency is a Pareto trade; it helps most on genuinely ambiguous questions.
- **Fix:** Keep it OFF by default (it is). Turn on only for workloads where you see inconsistent answers across repeated runs.

## Observability

- `result["claims"]` — list of `{text, verified}`. Inspect this first when accuracy drops.
- `result["unverified"]` — subset passed to the iteration re-search.
- `result["iterations"]` — 0 = first pass was clean; 1+ = verify triggered iteration.
- `eval/scorer.py` emits per-question latency + tokens in aggregate runs.

## Graceful degradation

Each toggle can be flipped independently. If verify is misbehaving, set
`ENABLE_VERIFY=0` and you're back to beginner semantics (minus HyDE).
