# research-assistant/eval

Reproducible scoring harness. Currently seeded with 3 questions — the
full 10-question eval set lands alongside THE-89.

## Run

```bash
export EXA_API_KEY=... GOOGLE_API_KEY=... OPENAI_API_KEY=...
make eval
```

Produces aggregate factuality and citation-precision scores over every
row in `dataset.jsonl`.

## Metrics

- **factuality_mean** — LLM-as-judge (GPT-5.4 mini) rates each candidate
  answer against the gold answer as 0 / 0.5 / 1.
- **citation_precision_mean** — proportion of required source domains
  (`must_cite_any`) that actually appear in the agent's answer.

## Dataset format

One JSON object per line in `dataset.jsonl`:

```json
{
  "id": "q1",
  "question": "...",
  "gold_answer": "...",
  "must_cite_any": ["example.com", "other.org"]
}
```

## Extending

Add rows to `dataset.jsonl`. Each question should be specific enough
that a correct answer cites identifiable sources. Target 10 rows across
AI/ML, finance, policy, and at least 3 questions where citation quality
(not just factuality) is the discriminator.
