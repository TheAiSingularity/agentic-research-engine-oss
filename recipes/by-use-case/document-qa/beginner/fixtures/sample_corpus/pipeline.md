# The research-assistant pipeline

## Stages

The production pipeline is an 8-node LangGraph:

    classify → plan → search → retrieve → fetch_url → compress → synthesize → verify

Each node is toggleable via an environment variable so leave-one-out
ablations are trivial. The whole thing runs against any
OpenAI-compatible endpoint via `OPENAI_BASE_URL` — Ollama, vLLM, SGLang,
or hosted providers — with no code changes.

## Adaptive verification

After the synthesizer produces a draft answer, Chain-of-Verification
(CoVe) splits it into atomic claims and checks each against the evidence
bundle. If any claim is unsupported, the pipeline re-searches for that
specific claim and regenerates. Iteration is bounded by
`MAX_ITERATIONS`, default 2.

FLARE detects hedged phrases in the draft ("the evidence does not
specify…") and triggers a targeted re-search for just that claim,
then regenerates the answer once with the fresh evidence merged in.

## Observability

Every LLM call's model, latency, prompt size, response size, and token
estimate land in `state["trace"]`. When the CLI finishes, it prints a
per-node and per-model summary. Nothing is sent to any SaaS telemetry
service — the trace stays on the machine.
