# `skills/` — reusable agent skills

Short, single-purpose capabilities agents can compose. Follows the pattern established by [heilcheng/awesome-agent-skills](https://github.com/heilcheng/awesome-agent-skills) (4.1K⭐ in 4 months — skills is a hot category).

## Scope

- Skills live here as small directories with a single responsibility: web-search, read-pdf, send-email, run-sql, summarize-long-doc, etc.
- Every skill declares its required permissions — maps cleanly to HermesClaw policy presets.
- Skills are language-agnostic by interface — same skill can have Python and Rust implementations.

## Status

**Seed skills land in Wave 4** by porting from [HermesClaw's existing skills library](https://github.com/TheAiSingularity/hermesclaw) and adding new ones as recipes need them.
