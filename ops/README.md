# ops/

Tactical maintainer notes. **Most users don't need to read these
files.** They exist for maintainers who want to republish the engine
— to PyPI, the official MCP registry, or the Anthropic plugin
marketplace — and need the exact commands, known pitfalls, and
failure modes we already hit.

| file | what it covers |
|---|---|
| [`submit-mcp-registry.md`](submit-mcp-registry.md) | publishing to `registry.modelcontextprotocol.io` via `mcp-publisher`: GitHub device-flow auth, `server.json` validation gotchas (description-length cap, PyPI ownership marker), JWT refresh |
| [`submit-claude-plugin.md`](submit-claude-plugin.md) | the `/plugin marketplace add <repo>` install flow, `.claude-plugin/marketplace.json` + `plugin.json` layout, end-to-end validation inside Claude Desktop / Cursor / Continue |
| [`submit-community-directories.md`](submit-community-directories.md) | auto-discovery timing for glama.ai, mcp.so, pulsemcp.com, claudemarketplaces.com; escalation issue templates if we're missing after 48 h |

## Why this lives in `ops/` and not `docs/`

`docs/` is for end-users (architecture, domains, plugins, self-learning,
how-it-works). `ops/` is for the person preparing a release. Different
audience; keeping them separate so the public-facing docs index reads
cleanly.
