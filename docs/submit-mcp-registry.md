# Submission guide — MCP registry (registry.modelcontextprotocol.io)

Gets the `agentic-research` server listed in the official MCP registry
at <https://registry.modelcontextprotocol.io>. Once listed, every
MCP-aware client (Claude Desktop, Cursor, Continue, custom agents) can
discover + install it.

**Two-step flow:** (1) publish the package to PyPI, (2) register the
metadata. **~10 minutes** of your time.

## TL;DR

```bash
# One-time: PyPI account + token
pip install twine build
python -m build                          # creates dist/*.whl + dist/*.tar.gz
twine upload dist/*                      # uploads to PyPI (asks for API token)

# One-time: MCP registry auth
brew install mcp-publisher
mcp-publisher login github               # GitHub device-flow

# Publish
mcp-publisher publish                    # uses ./server.json at repo root
```

That's it. The server appears at
<https://registry.modelcontextprotocol.io> under
`io.github.TheAiSingularity/agentic-research`.

## Prerequisites

- **Python 3.12+** with `pip` working.
- **A PyPI account.** Free — <https://pypi.org/account/register/>.
- **A PyPI API token** scoped to this project. See step 2 below.
- **Homebrew** (for `brew install mcp-publisher`) OR the manual binary
  download from <https://github.com/modelcontextprotocol/registry/releases>.
- **A GitHub account** (you already have one — `TheAiSingularity`).

## Step-by-step

### 1. Verify the package builds

I've already done this locally:

```bash
cd /Users/rvk/Projects/agentic-ai-cookbook-lab
python -m build
ls -l dist/
# Expect:
#   agentic_research_engine-0.1.1.tar.gz      ← sdist
#   agentic_research_engine-0.1.1-py3-none-any.whl ← wheel
```

Both artifacts are small (~100 KB wheel, ~130 KB sdist — no heavy deps
bundled). The wheel was already smoke-tested in a fresh venv:

```bash
rm -rf /tmp/ar-check && python3.12 -m venv /tmp/ar-check
/tmp/ar-check/bin/pip install dist/*.whl
/tmp/ar-check/bin/agentic-research version
# → "engine v0.1.1"
```

### 2. Get a PyPI API token

1. Register / log in at <https://pypi.org>.
2. Go to <https://pypi.org/manage/account/token/>.
3. Click "Add API token."
4. Name: `agentic-research-engine-release`.
5. Scope: "Entire account" for the first publish; after that, scope it
   to just this project.
6. Copy the token (starts with `pypi-`). **You won't see it again.**
7. Store it somewhere secure (password manager).

### 3. Upload to PyPI

```bash
pip install --upgrade twine
twine upload dist/*
# Prompts for:
#   username: __token__
#   password: <paste the pypi- token>
```

If successful, the package is immediately live at
<https://pypi.org/project/agentic-research-engine/>.

**Verify:**
```bash
rm -rf /tmp/pypi-verify && python3.12 -m venv /tmp/pypi-verify
/tmp/pypi-verify/bin/pip install agentic-research-engine
/tmp/pypi-verify/bin/agentic-research version
# → "engine v0.1.1"
```

### 4. Install `mcp-publisher`

```bash
brew install mcp-publisher
# or:
curl -L "https://github.com/modelcontextprotocol/registry/releases/latest/download/mcp-publisher_$(uname -s | tr '[:upper:]' '[:lower:]')_$(uname -m | sed 's/x86_64/amd64/;s/aarch64/arm64/').tar.gz" | tar xz mcp-publisher
sudo mv mcp-publisher /usr/local/bin/
mcp-publisher --version   # confirm it's installed
```

### 5. Authenticate to the registry

```bash
cd /Users/rvk/Projects/agentic-ai-cookbook-lab
mcp-publisher login github
```

This opens GitHub's device flow:

```
1. Visit https://github.com/login/device
2. Enter the code: XXXX-YYYY
```

Open the URL, paste the code, authorize the `mcp-publisher` OAuth
app. Terminal will confirm `✓ Logged in as TheAiSingularity`.

### 6. Inspect the `server.json`

Already shipped at `/Users/rvk/Projects/agentic-ai-cookbook-lab/server.json`.
Double-check the fields look right for your account:

```bash
cat server.json | python3 -m json.tool | head -20
```

Key fields:
- `name: "io.github.TheAiSingularity/agentic-research"` — must match
  your GitHub username after `io.github.`
- `packages[0].identifier: "agentic-research-engine"` — must match
  the PyPI package name you just published
- `packages[0].version: "0.1.1"` — must match the PyPI version

### 7. Publish

```bash
mcp-publisher publish
```

Expected output:

```
✓ Read server.json
✓ Validated against schema 2025-12-11
✓ Confirmed PyPI package agentic-research-engine==0.1.1 exists
✓ Published to registry.modelcontextprotocol.io
  → https://registry.modelcontextprotocol.io/v0.1/servers/io.github.TheAiSingularity/agentic-research
```

### 8. Verify

```bash
curl -s "https://registry.modelcontextprotocol.io/v0.1/servers?search=agentic-research" | python3 -m json.tool
```

Should list our entry. Expected fields on the public API:
- `name`, `description`, `version`, `repository`, `packages`.

## Later: bumping to 0.1.2 (and beyond)

Every release cycle:

1. Bump `version` in `pyproject.toml`, `engine/__init__.py`,
   `server.json`, and `engine/mcp/claude_plugin/.claude-plugin/plugin.json`.
2. Update `CHANGELOG.md`.
3. `python -m build`.
4. `twine upload dist/*` to PyPI.
5. `mcp-publisher publish` (uses the updated `server.json`).
6. `git tag -a v0.1.2 -m "..."` and push.
7. `gh release create v0.1.2 ...`.

## Known pitfalls

| symptom | cause | fix |
|---|---|---|
| `twine` asks for username/password | no `__token__` convention | username is literally `__token__` (two underscores each side); password is the token string |
| `mcp-publisher publish` says "PyPI version not found" | PyPI's CDN hasn't propagated yet | wait 2 minutes and retry |
| `login github` can't open browser | headless session | copy the URL + code manually; the flow works on any machine |
| `server.json` schema fails | stale $schema URL | the spec evolves; use the URL from <https://modelcontextprotocol.io/registry/quickstart> current as of the week you're publishing |
| Name conflict on PyPI (`agentic-research-engine` already taken) | someone else squatted it | fall back to `agentic-research-engine-oss`; update `pyproject.toml:name` + `server.json:packages[0].identifier` + rebuild |

## Why we don't ship an npm version too

Our engine is Python-only (LangGraph, core/rag, trafilatura, pypdf,
sentence-transformers all have hard Python deps). A Node wrapper that
just shells out to `python -m engine.mcp.server` would technically work
but adds a second release surface to maintain with no capability
benefit. Skip npm for now.

## Rollback

- **Yank a PyPI version**: <https://pypi.org/manage/project/agentic-research-engine/release/0.1.1/>
  → "Yank release" (hides it; doesn't delete).
- **Deprecate an MCP registry entry**: `mcp-publisher deprecate` (if
  supported by the current CLI version) OR update `server.json` with a
  `deprecated: true` field and re-publish.
- **Remove entirely**: registry entries are sticky by design; yank the
  PyPI version and the registry entry becomes unusable for installs
  but retains the historical record.
