<!--
Thanks for your contribution! Read CONTRIBUTING.md first if you haven't.
No Co-Authored-By trailers on commits — author-as-written-by.
-->

## What

<!-- One-sentence summary. -->

## Why

<!--
The problem this fixes / the capability this adds. Link to any related
issue (e.g. "closes #123").
-->

## How

<!-- Key implementation choices. Non-obvious trade-offs. -->

## Tests

<!--
- What new tests were added?
- Repo-wide test count before → after?
-->

## Checklist

- [ ] Tests pass locally:
      `PYTHONPATH=$(pwd) recipes/by-use-case/research-assistant/production/.venv/bin/python -m pytest core/rag recipes engine/tests -q`
- [ ] New env vars documented (in `engine/core/pipeline.py`, `engine/README.md`, or `docs/architecture.md`)
- [ ] `make smoke` works against Ollama (or explicit reason why not)
- [ ] No secrets in diff (API keys, tokens, `.env`)
- [ ] Commit messages follow the style (see `CONTRIBUTING.md`)
- [ ] No Co-Authored-By trailers
