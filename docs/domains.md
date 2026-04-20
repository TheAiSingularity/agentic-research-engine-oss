# Domain presets

A domain preset is a YAML file that tunes the pipeline for a specific
research workflow without code changes. The engine ships six:

| preset          | when to use |
|---              |---          |
| `general`       | the default; anything |
| `medical`       | disease / treatment / drug / trial questions |
| `papers`        | academic paper research (arXiv, preprints) |
| `financial`     | company fundamentals, SEC filings, market commentary |
| `stock_trading` | technical + news per-ticker (research, NOT execution) |
| `personal_docs` | Q&A over your own corpus, air-gapped |

Users pick a preset via the CLI's `--domain` flag, the TUI's dropdown,
the web GUI's dropdown, or the `/set-domain` Claude skill.

---

## What a preset can change

```yaml
name: preset-name
description: >
  Plain-English explanation. Shown in TUI/GUI pickers.

# Search behavior
searxng_categories:          # SearXNG category filter (e.g. science, news)
  - science
seed_queries:                # Appended to every sub-query by the search stage
  - "site:pubmed.ncbi.nlm.nih.gov"
rss_feeds:                   # Phase 7+ — domain-specific RSS sources
  - "https://example.com/feed.xml"

# Prompt deltas
synthesize_prompt_extra: |
  Additional rules appended to the synthesize prompt:
    - Rule one.
    - Rule two.

# Verification behavior
min_verified_ratio: 0.75      # Float 0..1. Answers below this trigger warnings.

# Retrieval overrides (env-var translated)
corpus_path: "/abs/path/or/empty"   # becomes LOCAL_CORPUS_PATH
top_k_evidence: 8                    # becomes TOP_K_EVIDENCE

# Specialist tools (for future node wiring)
tools_enabled:
  - pubmed_search
```

The loader supports YAML scalars, booleans, floats/ints, inline lists,
indented lists, and block scalars (`|` preserves newlines, `>` folds).
No PyYAML dependency.

---

## Using a preset

### CLI

```bash
engine ask "Summarize recent Paxlovid hospitalization evidence in vaccinated adults" \
  --domain medical --memory session
```

### Python

```python
from engine.core.domains import load, apply_preset
from engine.interfaces.common import run_query

preset = load("medical")
env_overrides = apply_preset(preset)   # dict of env-var -> value

# Apply overrides before invoking
import os
for k, v in env_overrides.items():
    os.environ[k] = v

result = run_query(question, domain="medical")
```

### MCP / Claude plugin

```
/research question: Paxlovid evidence in vaccinated adults
          domain: medical
```

(The `/set-domain` skill wraps this for you in plain English.)

---

## Writing your own preset

1. Create `engine/domains/<your-name>.yaml`.
2. Follow the schema above.
3. Run `engine domains list` — your preset should appear.
4. Test: `engine ask "test question" --domain <your-name>`.
5. Submit a PR (see `CONTRIBUTING.md`).

### Minimum viable preset

```yaml
name: legal_cases
description: >
  US legal case research. Biases search toward court opinions and
  legal databases.

searxng_categories: []
seed_queries:
  - "site:supreme.justia.com"
  - "site:courtlistener.com"
  - "site:casetext.com"

synthesize_prompt_extra: |
  DOMAIN: legal_cases. Extra rules:
    - Cite the court, year, and docket number when available.
    - Distinguish binding precedent from persuasive authority.
    - This is not legal advice.

min_verified_ratio: 0.85
top_k_evidence: 8
tools_enabled: []
```

Drop it at `engine/domains/legal_cases.yaml` and it's live.

---

## Design notes

### Why env-var translation for retrieval overrides

`engine.core.domains.apply_preset()` translates `corpus_path` and
`top_k_evidence` to environment variables (`LOCAL_CORPUS_PATH`,
`TOP_K_EVIDENCE`) that the pipeline already reads at module load. This
means we don't touch the pipeline to add a new override — add a field
to `DomainPreset`, wire it through `apply_preset()`, and the pipeline
picks it up on its next import.

### Why no `tools_enabled` wiring yet

Phase 6 ships the field but doesn't activate specialist tools. The
plumbing (a "tool registry" that searches, retrieves, or calls external
APIs per domain) is a future phase — it would wire into `_search` or
become a new pre-search node. Current presets note which tools they'd
want; contributors can add them in PRs.

### Why the parser is hand-rolled

PyYAML is 100+ k LOC and pulls in C extensions. The domain preset
format is tiny (scalars + lists + block scalars), so a 100-LOC parser
in pure Python keeps the `engine` install light without losing the
readability of YAML.

Contributors: if you need more YAML expressiveness than the hand parser
supports, the first 90 % of the fix is probably a bug report; the last
10 % is "just install PyYAML and route through it when the dep is
present." Either is a welcome PR.
