# `skills/` — standalone Claude skills

Self-contained prompt-only Claude skills that work in **any** Claude
install, with no MCP server, no pip-install, no external dependencies.
Each skill ships as a directory with a single `SKILL.md` (YAML
frontmatter + instructions) following the
[`agentskills.io`](https://agentskills.io) / Anthropic Claude skill
format.

These are distinct from the four skills bundled with the full engine at
[`engine/mcp/claude_plugin/skills/`](../engine/mcp/claude_plugin/skills/) —
those require our MCP server + pipeline. The ones here work on their
own.

## Shipped

| skill | one-liner | invoke |
|---|---|---|
| [`verify-answer`](verify-answer/SKILL.md) | Stress-test any answer against its evidence using Chain-of-Verification. Returns per-claim verdicts: VERIFIED / UNVERIFIED / CONTRADICTED. | `/verify-answer` |

## Install into Claude

Each skill is one Markdown file with YAML frontmatter. Install per the
[Claude skills documentation](https://code.claude.com/docs/en/skills):

```bash
# Option A — clone the repo, symlink the skill
git clone https://github.com/TheAiSingularity/agentic-research-engine-oss
mkdir -p ~/.claude/skills
ln -s $(pwd)/agentic-research-engine-oss/skills/verify-answer/SKILL.md \
      ~/.claude/skills/verify-answer.md

# Option B — copy just the file
curl -o ~/.claude/skills/verify-answer.md \
  https://raw.githubusercontent.com/TheAiSingularity/agentic-research-engine-oss/main/skills/verify-answer/SKILL.md
```

Inside Claude Desktop or Claude Code, the skill then fires on its
trigger phrases (see the skill's frontmatter) or via explicit
`/verify-answer`.

## Contribute a skill

See [`CONTRIBUTING.md`](../CONTRIBUTING.md). Rules for this directory
specifically:

1. **Prompt-only.** No MCP server, no external dependencies, no pip
   install required. If it needs tooling, it belongs in
   `engine/mcp/claude_plugin/skills/` instead.
2. **Single-purpose.** One clear job per skill. "Verify an answer"
   yes; "verify an answer and also summarize it and also translate it"
   no.
3. **YAML frontmatter:** `name`, `description`, `triggers`, `license`,
   `author`, `version` (semver).
4. **Backlink** to the full engine in the body where the automated
   version is relevant — helps users discover the deeper integration.
