# Runbook — trading-copilot/production

Symptom → likely cause → fix.

## "No candidates fire on any ticker, but beginner ran fine"

- **Cause:** Step critic rejected analyze output (check `result["critic_notes"]`). Some small models over-trigger the redo verdict on concise candidate lines.
- **Fix:** Inspect one run. If the candidates were reasonable but the critic rejected anyway, bump `MODEL_CRITIC` up a tier (e.g., gemma4:e4b on Mac, Qwen3.6-35B on VM) — or set `ENABLE_STEP_VERIFY=0` for this workload.

## "skeptic drops every candidate even obvious ones"

- **Cause:** Self-consistency is surfacing one reasonable reject among 3 samples and landing on minority.
- **Fix:** Drop `CONSISTENCY_SAMPLES` to 1, or set `ENABLE_CONSISTENCY=0`, then investigate whether the skeptic model is calibrated for your rule set. Alternative: use a stronger `MODEL_SYNTHESIZER`.

## "`_verify_alerts` drops every alert"

- **Cause:** Verifier model is too strict on "SUPPORTED" — it wants a direct quote from evidence, our alerts reason about implications.
- **Fix:** Soften the verify prompt or set `ENABLE_VERIFY=0` temporarily. Longer-term: switch `MODEL_VERIFIER` to a larger model.

## "PRAW credentials not working"

- **Cause:** OAuth setup complex; credentials need to be for a Reddit "script" app, not a "web app".
- **Fix:** Create app at https://www.reddit.com/prefs/apps (type: "script"), use client_id (under the app name) + client_secret.
- **Fail mode:** With creds missing or invalid, `_fetch_social` returns `[]` silently (no exception) — the pipeline continues without social context.

## "yfinance keeps timing out or returning empty"

- **Cause:** Yahoo Finance rate-limit wall. Known issue in 2026.
- **Fix:** Wait 5–15 min. The beginner tier's `_price_cache` helps — production reuses it. If persistent, alternative: `alpaca-py` (free IEX endpoint — new code but drop-in).

## "Critic feedback mentions 'news is sparse' on every ticker"

- **Cause:** SearXNG news query returning few hits. Usually the query format (`"{ticker} stock"`) is too generic.
- **Fix:** Improve the query — add company name (`"{ticker} {company_name} stock news"`) via a per-ticker lookup. Or check that SearXNG's news engines (Google News, Bing News) are enabled in `scripts/searxng/settings.yml`.

## "Ollama stalls on the verify_alerts pass"

- **Cause:** Each alert's claim-list prompt includes snapshot + news; with ≥3 alerts the context can exceed Ollama's default 2048-token window.
- **Fix:** Raise `OLLAMA_CONTEXT_LENGTH` on the daemon. Or reduce `NUM_NEWS_PER_TICKER` (default 5 → 3).

## "Graph exits immediately with 0 candidates"

- **Cause:** Watchlist is empty (validation stripped all) or prices all errored.
- **Fix:** Inspect `result["watchlist"]`, `result["prices"]`. Common cause: yfinance rate-limit (see above) or a typo in `watchlist.example.yaml`.

## Observability — what to print when debugging

```python
result = build_graph().invoke({})
print("watchlist:", result["watchlist"])
print("critic_notes:", result.get("critic_notes", []))
for c in result.get("candidates", []):
    print("  candidate:", c)
for a in result.get("alerts", []):
    print("  alert:", a["ticker"], a.get("vote_detail"))
for v in result.get("verified_alerts", []):
    print("  verified:", v["ticker"], v["n_claims"])
```

The state field names are stable across runs; they're part of the recipe's public contract.
