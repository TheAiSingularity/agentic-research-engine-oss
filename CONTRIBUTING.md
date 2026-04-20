# Contributing

Thanks for your interest in contributing. This project is positioned as
**the best $0 local research agent** — open-source end-to-end,
reproducible, privacy-preserving, honestly positioned against closed
frontier. Every PR helps that positioning hold up.

Three principles we actually enforce:

1. **Honesty.** If the pipeline can't do X, we say so. No marketing
   claims without measurements. Numbers in READMEs are what we actually
   got from `engine/benchmarks/runner.py`, not hopes.
2. **Privacy by default.** Nothing leaves the user's machine unless the
   user explicitly routes to a cloud backend via `--api-key`.
3. **Runs on a laptop.** If a feature requires a GPU VM, it's opt-in
   and clearly labeled. The default experience works on an Apple M4 Pro
   (or newer Intel/Linux equivalent).

---

## Ways to contribute

| contribution | effort | blast radius |
|---|---|---|
| **Good first issue** (label: `good-first-issue`) | 1–3 hours | localized |
| **Bug fix** with a reproducing test | few hours | bounded |
| **New domain preset** — `engine/domains/<name>.yaml` | 1–2 hours | additive |
| **New skill or plugin** for the Claude plugin bundle | few hours | additive |
| **New MCP tool** in `engine/mcp/server.py` | half day | API surface grows |
| **Benchmark fixture** — new SimpleQA / BrowseComp mini entries | 1–2 hours | additive |
| **New pipeline node** | multi-day, needs RFC | pipeline-wide |
| **Major architectural change** | needs RFC first | repo-wide |

### RFCs

For pipeline changes or anything affecting more than one module, open a
GitHub issue with the `rfc` label before writing code. Describe:

- the problem (with a concrete example)
- the proposed solution
- alternatives considered
- impact on existing tests and users

The maintainers will respond within ~1 week. If silence goes longer than
two weeks, ping us on the issue.

---

## Development setup (M1/M2/M3/M4 Mac)

```bash
# 1. Clone
git clone https://github.com/TheAiSingularity/agentic-ai-cookbook-lab
cd agentic-ai-cookbook-lab

# 2. Local stack
brew install ollama                 # or https://ollama.com/download
ollama pull gemma3:4b nomic-embed-text
(cd scripts/searxng && docker compose up -d)

# 3. Python env
cd engine && make install           # creates .venv + installs deps

# 4. Tests
make test                           # mocked tests, no API key needed

# 5. Live smoke (optional)
make smoke                          # runs the pipeline end-to-end against Ollama
```

### Linux (Intel/AMD + optional GPU)

```bash
# Use scripts/setup-vm-gpu.sh if you have a GPU; otherwise same flow
# as Mac but swap Ollama install for your package manager.
```

---

## Coding standards

- **Python 3.12+** with full type hints on public APIs.
- **4-space indentation** everywhere; follow existing file style.
- **f-strings** — no `%` or `.format`.
- **pathlib** for filesystem work.
- **No comments restating what code does.** Write doc-comments for
  non-obvious "why" choices.
- **No docstring on every function.** The module docstring explains the
  module; individual functions get docstrings only when they're
  non-obvious.
- **No Co-Authored-By trailers** on commits. This repo uses
  author-as-written-by (`TheAiSingularity`).

### Testing

- **Every PR ships tests for the new behavior.** No exceptions for
  "trivial" changes.
- **Tests must be mocked** — no network, no LLM calls, no model
  downloads during `pytest`. Use the existing fixtures
  (`engine/tests/test_interfaces.py::patched_graph`,
  `test_production_main.py::patched`) as templates.
- **Live integration smokes** are separate (`make smoke`, per-recipe
  `make smoke`) and optional in CI.

### Style enforcement

We don't run a formatter (yet). Match the existing style in the file
you're editing. If you think a file should be auto-formatted, open an
issue — don't reformat whole files in the same PR as a feature change.

---

## PR checklist

Before opening a PR, verify:

- [ ] New tests cover the new behavior (see `engine/tests/` for style).
- [ ] `pytest` passes locally from the repo root: `PYTHONPATH=$(pwd)
      recipes/by-use-case/research-assistant/production/.venv/bin/python
      -m pytest core/rag recipes engine/tests -q`
- [ ] Repo count: tests did not decrease. If your PR deletes behavior,
      tests that exercised that behavior are removed in the same PR.
- [ ] New env vars are documented in `engine/core/pipeline.py` header OR
      `engine/README.md` env var table OR `docs/architecture.md`.
- [ ] Live smoke runs without errors against Ollama (`make smoke`).
- [ ] No secrets committed (`.env`, API keys, tokens). The repo-wide
      `.gitignore` has conservative defaults; double-check your diff.
- [ ] Commit messages follow the style (see below).
- [ ] PR description follows the template.

### Commit message style

Look at the recent commit log (`git log --oneline -20`) for the pattern.
Short summary on line 1 (≤70 chars), blank line, paragraphs explaining
the what + why + how. Example:

```
Phase 6: domain presets + 5 worked examples

Six shipped domain presets + loader + 5 end-to-end worked examples
that double as integration-test fixtures in Phase 8.

  engine/core/domains.py     (~170 LOC)
    DomainPreset dataclass — …

  engine/domains/medical.yaml         — PubMed/Cochrane/NEJM bias, …

Tests: 229 → 245 repo-wide green.
```

No Co-Authored-By trailer. Author-as-written-by.

### PR description template

```markdown
## What

One-sentence summary.

## Why

The problem this fixes / the capability this adds. Link to any related
issue.

## How

Key implementation choices. Non-obvious trade-offs.

## Tests

What new tests were added. Repo-wide test count before → after.

## Checklist

- [ ] Tests pass locally
- [ ] New env vars documented
- [ ] Live smoke works
- [ ] No secrets in diff
```

---

## Good-first-issue candidates

These are curated for first-time contributors. They're small, scoped,
and touch one area of the codebase:

1. **Add a domain preset** for a specific field (e.g. `legal_cases`,
   `scientific_policy`, `crypto_research`). See `docs/domains.md`.
2. **Add a new BrowseComp-Mini or SimpleQA-Mini fixture question** to
   `engine/benchmarks/*.jsonl`. Hand-verify the gold answer; submit
   with your name in the YAML comments.
3. **Better CLI help text** — the `--help` output could be more
   comprehensive. See `engine/interfaces/cli.py`.
4. **Plugin manager UI in the TUI** — add a `p` keybind that opens a
   plugin-installed list. Scaffold in `engine/interfaces/tui.py`.
5. **Unit tests for `_chunk_text` edge cases** — what happens with
   Windows `\r\n`? With code blocks? With Markdown tables? Add tests
   to `core/rag/tests/test_corpus.py`.
6. **Dark / light theme toggle in the Web GUI** — `engine/interfaces/
   web/static/app.css` is dark-only today.
7. **Improve error messages** when Ollama/SearXNG is down — the
   current errors are raw exceptions; wrap them with actionable
   recovery hints.
8. **Reddit / StackOverflow seed_queries domain preset** — `community`
   preset that biases search toward user-generated content.

Pick one, open a PR. If you want scope guidance before starting, open an
issue asking "is this a good scope for <issue-title>?"

---

## Plugin submission lane

If you're writing a plugin to ship via `engine plugins install`:

1. Follow the format in `docs/plugins-skills.md`.
2. Test locally: `engine plugins install file:$(pwd)/your-plugin`.
3. Push to GitHub (public repo).
4. Open a PR against this repo that:
   - adds a link to your plugin in a new `docs/plugin-catalog.md`
     (we'll create it with the first submission)
   - notes the expected trigger / use-case
5. We'll review for safety (forbidden-symbols scan, obviously-harmful
   behavior) and merge.

We don't host third-party plugin code. The plugin-catalog link system
keeps your plugin in your control; users install it on their own
machines from your repo.

---

## Domain-preset submission lane

Adding a new domain preset is the lightest way to contribute useful
capability:

1. Copy `engine/domains/general.yaml` to `engine/domains/<your-name>.yaml`.
2. Fill in `seed_queries`, `synthesize_prompt_extra`, and the verification
   strictness that suits your domain.
3. Add one test case to `engine/tests/test_domains.py` asserting
   preset-specific invariants (e.g. for `legal_cases`, assert that a
   court-name bias term is in `seed_queries`).
4. Optionally: add a worked example in `engine/examples/<NN>_your_domain.md`
   following the existing 5 examples' template.
5. Open a PR. No RFC needed for a new preset.

---

## Reporting bugs

Open a GitHub issue with:

- What you were trying to do
- What actually happened (including full error / trace output)
- Output of `engine version` and `python --version`
- Output of `ollama list` (if a local-inference bug)
- Minimal reproducer if possible

Use the `bug` label.

---

## Security

If you find a vulnerability (e.g. a plugin loader bypass, a prompt-
injection vector that escapes domain constraints, a memory-store leak
across domain scopes), **don't** open a public issue. Email the
maintainers directly (security contact populated when repo goes public
in Phase 9) with the report. We'll acknowledge within 72 hours.

---

## Code of Conduct

Short version: be kind, be honest, assume good faith, argue ideas not
people.

Full Contributor Covenant v2.1 in [`CODE_OF_CONDUCT.md`](CODE_OF_CONDUCT.md).

---

## License

By contributing, you agree your contributions are licensed under the
repo's MIT license. See [`LICENSE`](LICENSE).

---

## Maintainers

- **TheAiSingularity** (project owner)

Everyone else who's contributed is listed in `git log --format='%an' |
sort -u`.
