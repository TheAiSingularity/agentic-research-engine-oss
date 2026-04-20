# Self-learning: trajectory logging + memory retrieval

The engine learns in a privacy-preserving, fully-local way: every query
is logged as a trajectory, and subsequent related queries retrieve those
trajectories and surface their summaries as context.

**No model fine-tuning happens in v1.** The data is collected and
structured so that a future LoRA refresh loop can be added when GPU
access and trajectory volume justify it. For now, the benefit is
cheap-retrieval of your own past research.

---

## What a trajectory contains

```python
@dataclass
class Trajectory:
    query_id:           str
    timestamp:          float
    question:           str
    domain:             str
    final_answer:       str
    verified_claims:    list[dict]   # [{text, verified}]
    unverified_claims:  list[str]
    evidence_urls:      list[str]
    iterations:         int
    question_class:     str
    tokens_est:         int
    latency_s:          float
```

Every pipeline run produces one. The full dict is stored as a JSON blob
so future schema changes don't require a migration — you deserialize what
you get.

---

## Storage

Three modes, chosen per-query via `--memory` CLI flag or the MCP
`research(memory=…)` tool argument:

| mode           | store | persists? |
|---             |---    |---        |
| `off`          | nothing | no |
| `session`      | in-process Python list | no |
| `persistent`   | SQLite at `~/.agentic-research/memory.db` | yes |

SQLite schema (persistent mode):

```sql
CREATE TABLE trajectories (
  query_id       TEXT PRIMARY KEY,
  timestamp      REAL NOT NULL,
  question       TEXT NOT NULL,
  domain         TEXT NOT NULL,
  payload        TEXT NOT NULL        -- JSON of the full Trajectory
);
CREATE INDEX traj_domain ON trajectories(domain);
CREATE INDEX traj_ts ON trajectories(timestamp DESC);

CREATE TABLE embeddings (
  query_id       TEXT PRIMARY KEY REFERENCES trajectories(query_id) ON DELETE CASCADE,
  vec            BLOB NOT NULL        -- struct-packed float32 vector
);
```

You can inspect the database with any SQLite browser. You can delete
rows by hand. You can query it with `sqlite3 ~/.agentic-research/memory.db
"SELECT question, domain FROM trajectories WHERE domain='medical'"`.

---

## Retrieval

On every query, if memory is on:

1. The question is embedded (same embedder as `core.rag` — honors
   `OPENAI_BASE_URL` + `EMBED_MODEL`, so on Mac-local this uses
   `nomic-embed-text` via Ollama).
2. Cosine similarity is computed against every stored trajectory
   embedding (linear scan — fine at < 10 000 rows).
3. Trajectories with cosine ≥ `MEMORY_MIN_SCORE` (default 0.55) are
   returned, sorted by score descending.
4. Top-K (default 3) are injected as context into the question:

       {original question}

       (Context from prior related research:
         - (0.87) prior question 1
           → prior answer 1 (trimmed to 200 chars)
         - (0.73) prior question 2
           → prior answer 2
       )

5. The pipeline runs as usual. The original (un-augmented) question is
   what gets recorded in the new trajectory — not the augmented version.

---

## Resetting memory

Three ways:

```bash
engine reset-memory                          # CLI
```

```
/research reset-memory                       # Claude plugin
```

```bash
rm ~/.agentic-research/memory.db             # the nuclear option
```

Use domain filtering on the SQLite directly if you want to wipe only one
domain:

```bash
sqlite3 ~/.agentic-research/memory.db \
  "DELETE FROM trajectories WHERE domain='personal_docs'"
```

---

## Transparency properties

- **No outbound network.** Embeddings go through the same
  `OPENAI_BASE_URL` you've configured for the pipeline. If that's Ollama,
  embeddings are local. If you've explicitly routed to cloud OpenAI via
  `--api-key`, embeddings go there — along with the question itself.
- **No telemetry.** No engine component records to any external service.
- **Inspectable.** Open the SQLite file in any tool.
- **Scoped.** Each trajectory is tagged with a `domain`. Retrieval can be
  domain-restricted, so medical queries don't accidentally pull
  stock-trading trajectories into context.
- **Bounded.** `MEMORY_MIN_SCORE=0.55` by default keeps loosely-related
  trajectories out of context. Raise it to 0.75+ if you only want
  near-duplicate retrievals.

---

## Why not LoRA fine-tuning in v1?

Three honest reasons:

1. **Fine-tuning on too-little data degrades quality.** A typical user
   might have 10–50 trajectories after a week of casual use. A useful
   LoRA refresh needs thousands of diverse examples.
2. **Training loops are ops-heavy.** An MLX LoRA run on M4 Pro takes
   2–6 hours per refresh; scheduling, dataset curation, eval-regression
   checks — none of that is needed for v1's memory-retrieval value.
3. **Privacy concerns.** Fine-tuning mixes trajectories into the model
   weights; memory retrieval keeps them in clearly-separated storage.
   Per-domain deletion is trivial with retrieval; weight surgery is not.

Phase 10+ will add opt-in LoRA fine-tuning when (a) GPU access is
confirmed and (b) users have accumulated enough trajectories to make the
training worthwhile.

---

## Future work (not in v1)

- **Cross-session memory sharing** — export/import trajectories between
  machines or users (opt-in, encrypted export).
- **Trajectory quality filter** — automatically prune low-verified or
  contradictory trajectories so they don't poison retrieval.
- **Memory consolidation** — periodic LLM pass that collapses highly-
  similar trajectories into a single "memory" with multiple source IDs.
- **Multi-user memory stores** — teams that want to share research
  histories while keeping personal queries separate.

Each of these is a welcome PR; see `CONTRIBUTING.md`.
