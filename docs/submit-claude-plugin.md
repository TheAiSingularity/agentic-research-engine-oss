# Submission guide — Anthropic Claude plugin marketplace

How to get the `agentic-research` plugin discoverable inside Claude
Desktop and Claude Code. **~5 minutes** of your time.

## TL;DR

The repo ships a top-level [`marketplace.json`](../marketplace.json)
that declares one plugin at `engine/mcp/claude_plugin/`. Any Claude
user runs two slash-commands to install it:

```
/plugin marketplace add https://github.com/TheAiSingularity/agentic-research-engine-oss
/plugin install agentic-research
```

That's the distribution path. No central Anthropic submission form to
wait on — the marketplace discovery happens via the public `marketplace.json`
on the repo.

## Step-by-step

### 1. Confirm the public repo is up-to-date

```bash
cd /Users/rvk/Projects/agentic-ai-cookbook-lab
git log --oneline -1      # latest commit should be v0.1.1 tag-commit
gh repo view TheAiSingularity/agentic-research-engine-oss --json visibility,url
# expect: "PUBLIC" + the GitHub URL
```

If anything is missing, `git push origin main` + `git push origin v0.1.1`.

### 2. Smoke-test the plugin locally before announcing

Inside **Claude Desktop** or **Claude Code** (requires Claude 2026+
with the plugins feature enabled):

```
/plugin marketplace add https://github.com/TheAiSingularity/agentic-research-engine-oss
```

Claude will clone the repo, read `marketplace.json`, and register the
`agentic-research` plugin as available.

```
/plugin install agentic-research
```

This copies the plugin contents to `~/.claude/plugins/cache/agentic-research/`
and wires up the `engine` MCP server per `plugin.json`.

```
/plugin list
```

Should show `agentic-research` with status `enabled`.

```
/research What is Anthropic's contextual retrieval and what percentage reduction did they report?
```

Should trigger the `research` skill, which calls the MCP server's
`research(...)` tool, which runs the full pipeline end-to-end.

### 3. If step 2 works, distribution is live

The plugin is now discoverable by anyone who:
- Runs `/plugin marketplace add <our-URL>` in Claude Desktop/Code
- Browses the community aggregators (see step 4)

### 4. Broaden discoverability via community aggregators

#### claudemarketplaces.com

Third-party but well-trafficked. Open an issue or PR on their GitHub:

```
Title: Submit: TheAiSingularity / agentic-research-engine-oss
Body:
  name: agentic-research
  repo: https://github.com/TheAiSingularity/agentic-research-engine-oss
  plugin_path: engine/mcp/claude_plugin
  description: The best $0 research agent that runs on a laptop.
  categories: research, rag, local-llm, verification
  marketplace.json: https://raw.githubusercontent.com/TheAiSingularity/agentic-research-engine-oss/main/marketplace.json
```

#### claudeskills.info / kissmyskills.com

Same pattern — submit via their repos' issue trackers.

#### Anthropic Discord `#community-plugins`

Post a short announcement with:
- What the plugin does (one sentence)
- Install command
- Demo GIF or screenshot
- Link to the repo

### 5. Watch for an "Anthropic Verified" badge (optional, later)

Anthropic operates a separate review process for the blue verified
badge. It's based on maturity signals:
- Repo age + activity
- Passing CI (our [`.github/workflows/engine-tests.yml`](../.github/workflows/engine-tests.yml) is already green)
- Community adoption (stars, issues, contributors)
- No security incidents

There's no form to apply — they pick plugins from the active set that
meets their criteria. Just run a good repo and it tends to happen
organically.

## Known pitfalls

| symptom | likely cause | fix |
|---|---|---|
| `/plugin install agentic-research` says "MCP server failed to start" | the user doesn't have `agentic-research-engine` on their Python path | tell them to `pip install agentic-research-engine` — the plugin.json assumes the PyPI package is installed |
| `/research` hangs | Ollama or SearXNG down on their machine | our plugin.json's env vars default to Ollama + local SearXNG; users running cloud-OpenAI need to override `OPENAI_BASE_URL` + `OPENAI_API_KEY` via Claude Desktop's plugin env |
| Plugin doesn't appear after `marketplace add` | user is running an old Claude version | requires Claude 2026+ with plugin support |
| Claude can't find `python` | macOS users without `python` on PATH | document that they need Python 3.12+ and Ollama; link to our root README quickstart |

## How the plugin finds our MCP server

`plugin.json` has:

```jsonc
"mcpServers": {
  "engine": {
    "command": "python",
    "args": ["-m", "engine.mcp.server"],
    "env": { "OPENAI_BASE_URL": "http://localhost:11434/v1", ... }
  }
}
```

This works **if the user has our package pip-installed**, because the
Python import path resolves `engine.mcp.server`. We publish as
`agentic-research-engine` on PyPI specifically so:

```
pip install agentic-research-engine
```

gives the user the `engine` importable package + a console-script
`agentic-research-mcp` if they'd rather invoke that directly.

After they install the plugin, if the MCP server fails to start with
`ModuleNotFoundError: engine`, the fix is `pip install agentic-research-engine`.

## Rollback

To un-distribute: delete `marketplace.json` from the repo (or remove
the `agentic-research` entry). Users who already installed keep their
copy; new installs fail.

```bash
git rm marketplace.json
git commit -m "unlist agentic-research plugin from marketplace"
git push
```
