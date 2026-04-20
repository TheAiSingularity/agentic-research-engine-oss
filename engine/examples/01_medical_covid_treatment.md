# Example 01 — Medical: COVID-19 antiviral treatment evidence

Domain: `medical` · Expected wall-clock on Mac M4 Pro with Gemma 3 4 B: ~60-90 s.

## The question

> What is the current evidence that Paxlovid reduces COVID-19
> hospitalization risk in vaccinated adults, and how does it compare to
> molnupiravir on the same endpoint?

## Command

```bash
cd engine
make install
ollama pull gemma3:4b nomic-embed-text
(cd ../scripts/searxng && docker compose up -d)
make cli Q="What is the current evidence that Paxlovid reduces COVID-19 hospitalization risk in vaccinated adults, and how does it compare to molnupiravir on the same endpoint?"
# same as: python -m engine.interfaces.cli ask "…" --domain medical --memory session
```

Or from the Claude plugin:

```
/set-domain medical
/research What is the current evidence that Paxlovid reduces COVID-19 hospitalization risk in vaccinated adults, and how does it compare to molnupiravir on the same endpoint?
```

## What the pipeline does

1. **classify** → `multihop` (comparison across two drugs + evidence-grade nuance).
2. **plan** → three sub-queries:
   - Paxlovid hospitalization reduction in vaccinated adults meta-analysis
   - molnupiravir hospitalization outcome randomized trial vaccinated
   - head-to-head Paxlovid vs molnupiravir comparison
3. **search** → SearXNG query biased to `site:pubmed.ncbi.nlm.nih.gov`, `site:cochrane.org`, `site:nejm.org` via the `medical.yaml` seed_queries. Returns peer-reviewed abstracts + Cochrane systematic reviews.
4. **retrieve** → hybrid BM25 + dense over the returned snippets; top-8 (medical preset sets TOP_K_EVIDENCE=8).
5. **fetch_url** → trafilatura pulls full abstracts/articles where available; paywalled articles return snippet only.
6. **compress** → one-sentence-per-chunk compression keeping study type (RCT / meta-analysis / cohort) and sample size.
7. **synthesize** → answers with inline [N] citations, separating animal-model / in-vitro / clinical phases per the medical preset's prompt_extra.
8. **verify** → CoVe claim decomposition. Medical preset has `min_verified_ratio: 0.75` — any answer whose verified/total ratio is below 75 % triggers explicit warning.

## Expected output shape

```
Q: What is the current evidence that Paxlovid reduces COVID-19
   hospitalization risk in vaccinated adults, and how does it compare
   to molnupiravir on the same endpoint?

[class: multihop]

A: In adults with prior vaccination, Paxlovid (nirmatrelvir-ritonavir)
   has demonstrated a statistically significant reduction in COVID-19-
   related hospitalization relative to placebo in multiple cohort
   studies. A 2023 retrospective cohort published in NEJM [1] reported
   a roughly 44% relative reduction in hospitalization among
   vaccinated high-risk adults.

   Molnupiravir's effect on hospitalization among vaccinated adults
   has been more equivocal. The PANORAMIC trial (UK, 2022-2023) found
   no statistically significant reduction in hospitalization rate
   among vaccinated adults who received molnupiravir compared with
   usual care [2], though it did shorten time-to-recovery.

   Head-to-head randomized comparison is limited. A 2024 meta-
   analysis [3] that pooled observational studies suggested Paxlovid
   had a larger hospitalization-reduction effect than molnupiravir
   in vaccinated adults, but the authors note high inter-study
   heterogeneity and limited RCT data for the molnupiravir arm.

   This is not medical advice; prescribing decisions should be made
   by a licensed clinician.

Cited sources:
  [1] ● https://www.nejm.org/doi/10.1056/NEJMoa2302729
        NEJM cohort study, n=XXXX vaccinated high-risk adults, 2023
  [2] ● https://www.thelancet.com/panoramic-trial
        PANORAMIC RCT, The Lancet, 2022-2023
  [3] ○ https://www.cochrane.org/cdsr/paxlovid-vs-molnupiravir
        Cochrane pooled analysis, 2024

Hallucination check — 5/5 claims verified
  ✓ Paxlovid reduced hospitalization ~44% in vaccinated cohort (NEJM 2023)
  ✓ PANORAMIC found no significant hospitalization reduction for molnupiravir in vaccinated adults
  ✓ Meta-analysis pooled observational studies
  ✓ Paxlovid showed larger effect than molnupiravir in vaccinated adults in the meta-analysis
  ✓ RCT evidence for molnupiravir in vaccinated adults is limited

Trace (per-node totals):
  search      27.4 s  (3 subqueries across PubMed + Cochrane)
  fetch_url   12.1 s  (8 URLs, 6 successfully extracted)
  compress     9.8 s
  synthesize   6.3 s
  verify       7.5 s
  plan         5.1 s
  classify     3.0 s
  retrieve     0.7 s

  total: 71.9 s · ~14200 tokens · iterations=1
```

## Reproduction notes

- The exact numbers (~44 %, PANORAMIC findings, 2024 meta-analysis title) depend on what the SearXNG federation returns at query time. Your answer may differ; the **structure** (separate blocks per drug, explicit evidence grade, clinician-referral disclaimer) is the reproducible part.
- With `memory persistent`, the second run of a related medical query will see the first answer as context — this materially improves follow-up questions like "what about immunocompromised adults?"
- To run this offline, build a medical corpus first:

  ```bash
  python scripts/index_corpus.py build ~/medical-pdfs --out ~/medical.idx
  export LOCAL_CORPUS_PATH=~/medical.idx
  ```

  `medical.yaml` does not set a corpus_path by default; users who curate their own literature opt in via the env var.

## Why this is hard

4 B-parameter models tend to flatten evidence nuance ("PANORAMIC showed molnupiravir reduced hospitalization" — wrong subgroup) when given too much context. Three pipeline features defend against that: W6 three-case synthesize prompt (refuses rather than invents), CoVe verify (flags any claim not supported by compressed evidence), and the `medical.yaml` preset's 75 %-verified floor (answer is surfaced to user only if CoVe passes).
