# Plugins + skills

The engine treats external plugins as a first-class extension mechanism.
Users install plugins from GitHub, local paths, or remote marketplace
manifests. Contributors write their own plugins to share domain-specific
skills, search strategies, or MCP servers with the community.

---

## What's a plugin, what's a skill, what's an MCP server

Clear terms so we avoid the confusion that exists in the wild April 2026 ecosystem:

- **MCP server** — a process that speaks the Model Context Protocol over
  stdio or SSE. Exposes "tools" that any MCP client (Claude Desktop, Cursor,
  Continue, our engine) can call. Written in any language.
- **Skill** — a single Markdown file with YAML frontmatter
  (`name`, `description`, `triggers`). Body is the system prompt /
  procedure Claude follows when the skill fires. Same file format in both
  Anthropic's Claude plugin spec and Nous Research's
  `agentskills.io` / Hermes format.
- **Claude plugin** — a **container**. One directory with
  `.claude-plugin/plugin.json` that bundles zero or more skills, agents,
  MCP servers, and hooks. This is what you publish to
  `platform.claude.com/plugins/submit`.
- **Marketplace** — `claude.com/plugins`, plus third-party aggregators
  (`claudemarketplaces.com`, `claudeskills.info`, `mcp.so`, etc.).
  **Only `claude.com/plugins` is Anthropic-official**; the rest are
  community discovery sites.

---

## Installing plugins

### From the CLI

```bash
# Claude plugin from GitHub
engine plugins install gh:some-owner/agentic-research-medical@v0.3.0

# Local directory (testing your own plugin)
engine plugins install file:./my-plugin

# A single Hermes skill .md file
engine plugins install file:./my-skill.md

# A remote marketplace.json (Claude plugin spec)
engine plugins install https://example.com/marketplaces/research.json

# List installed plugins
engine plugins list

# Inspect metadata for one
engine plugins inspect <name>

# Remove
engine plugins uninstall <name>

# Wipe everything
engine plugins reset
```

### From the TUI

Press `p` to open the plugin manager pane. Paste the source URI into the
input box; Enter installs; Delete uninstalls the selected row.

### From the web GUI

Navigate to `/plugins` (Phase 7+). Same interactions as the TUI.

### From Claude Desktop / Claude Code

Use Anthropic's built-in plugin flow:

```
/plugin marketplace add <local-path-or-github-url>
/plugin install agentic-research
```

Our own plugin (`engine/mcp/claude_plugin/`) registers like this once
submitted to the official marketplace.

---

## Writing your first Claude plugin

Directory layout (minimum):

```
my-plugin/
├── .claude-plugin/
│   └── plugin.json
└── skills/
    └── my-first-skill.md
```

### `plugin.json`

```json
{
  "name": "my-plugin",
  "version": "0.1.0",
  "description": "What my plugin does in one sentence.",
  "author": { "name": "<your-name>" },
  "license": "MIT",
  "skills": ["skills/my-first-skill.md"],
  "mcpServers": {
    "my-tool": {
      "command": "python",
      "args": ["-m", "my_tool.server"]
    }
  }
}
```

Required fields: `name`, `version`. Everything else is optional but
strongly recommended. `name` must be kebab-case and globally unique in
the marketplace you publish to.

### A skill Markdown file

```markdown
---
name: my-first-skill
description: "One-line description of what this skill does."
triggers:
  - trigger phrase one
  - trigger phrase two
---

Instructions and procedures Claude follows when this skill fires.

1. Step one.
2. Step two.
3. When calling an MCP tool, use `mcp__<server-name>__<tool-name>` naming.

Don't editorialize beyond what the tool returns. Cite sources explicitly.
```

### Test it locally

```bash
# Point the engine at your local directory
engine plugins install file:$(pwd)/my-plugin

# Verify it was registered
engine plugins list

# Inspect
engine plugins inspect my-plugin
```

### Safety — what the installer rejects

The installer scans every text file for forbidden substrings before
writing to the registry. Anything matching these patterns is rejected:

- `eval(`, `exec(`, `__import__`
- `subprocess.Popen`
- `os.system(`
- `shutil.rmtree('/')`
- `/etc/passwd`

If you genuinely need one of these, fork `engine.core.plugins` and remove
the forbidden symbol from `FORBIDDEN_SYMBOLS`. Do not ship a plugin that
invites the install to fail — users won't install it twice.

---

## Writing a Hermes / agentskills.io skill

Hermes skills are single Markdown files. Same frontmatter as a Claude
skill; no containing `plugin.json` needed.

```markdown
---
name: my-hermes-skill
description: "One-line description."
version: 0.1.0
author: <your-name>
triggers:
  - invoke me
---

Procedure goes here.
```

Install:

```bash
engine plugins install file:/path/to/my-hermes-skill.md
```

The engine wraps the skill as a synthetic single-skill "plugin" in the
registry so both formats share the same storage + inspection UX.

---

## Submitting to marketplaces

### Anthropic Claude plugin marketplace (official)

1. Push your plugin repo to GitHub (public).
2. Submit at https://platform.claude.com/plugins/submit or the
   equivalent page inside Claude.
3. Anthropic reviews automated + (for verified badge) manual.
4. Listing cost: free. SLA: not published.

### MCP registry (official)

For MCP servers:

1. Publish to npm with `mcpName` set in `package.json` (format
   `io.github.<owner>/<server>`).
2. Authenticate: `mcp-publisher login` (GitHub OAuth device flow).
3. Register: `mcp-publisher publish`.
4. Metadata goes to `registry.modelcontextprotocol.io`; the binary stays
   wherever you host it (npm / ghcr / your own).

### Third-party aggregators

- `claudemarketplaces.com` — community aggregator, independently run.
- `claudeskills.info` — similar.
- `mcp.so` — MCP-focused directory.
- `kissmyskills.com` — third-party skills list.

These have their own submission flows (typically a PR to a GitHub repo).
**Use them for discoverability; never rely on them as primary
distribution** — they're unofficial and ownership can change.

---

## Our own plugin bundle

`engine/mcp/claude_plugin/` is a reference implementation. It bundles
the full research engine as a Claude plugin with four skills:

- `/research` — run a full research query
- `/cite-sources` — show sources behind the last answer
- `/verify-claim` — targeted CoVe verification
- `/set-domain` — route into medical/papers/financial/stock/personal_docs

Read `engine/mcp/claude_plugin/README.md` for the plugin-marketplace-
facing positioning copy.

---

## Debugging a plugin that fails to install

The installer emits a clear error at each rejection point:

```
[engine.plugins] rejected: forbidden symbols ['eval('] found in /path/to/skill.md
```

Fix the flagged content, re-run `engine plugins install file:…`. The
registry is idempotent — reinstalling the same plugin name overwrites
the previous copy cleanly.

If you're developing rapidly and don't want to re-install after every
edit, point `LOCAL_CORPUS_PATH` at the dev directory and edit in place
— the engine re-reads from disk each query.
