---
name: Plugin or domain-preset submission
about: Ship a new plugin, skill, or domain preset
title: "[plugin] "
labels: plugin
assignees: ''
---

## What kind of contribution

- [ ] A new **domain preset** (`engine/domains/<name>.yaml`)
- [ ] A new **skill** (single `.md` with YAML frontmatter)
- [ ] A new **plugin** (hosted in your own repo, linked from `docs/plugin-catalog.md`)
- [ ] A new **MCP tool** added to `engine/mcp/server.py`

## What it does

One-paragraph description. What trigger phrases or CLI invocations does
it respond to?

## Domain preset details (if applicable)

- Name:
- Search bias sources:
- Prompt deltas:
- `min_verified_ratio`:
- Safety constraints (if any):

## Plugin details (if applicable)

- Your plugin's GitHub repo URL:
- License (MUST be MIT or Apache 2.0 for inclusion in docs/plugin-catalog.md):
- Dependencies beyond the engine:

## Safety

- [ ] No forbidden symbols (see `engine.core.plugins.FORBIDDEN_SYMBOLS`).
- [ ] No network calls to hard-coded URLs that weren't user-supplied.
- [ ] No automatic plugin auto-install (see the engine's security model).

## Example output

Paste a real transcript showing your addition in action.

## Tests

- [ ] Added test invariants in `engine/tests/test_domains.py` (domain presets)
- [ ] Added an example under `engine/examples/` (optional but valuable)
