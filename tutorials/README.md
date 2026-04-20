# Tutorials — Google Colab runnable, end-to-end

Five worked tutorials covering the engine's main capabilities. Each
notebook is **self-contained** — open it in Colab, click through, done.
No local install, no Docker, no Ollama required on the free Colab tier.

<!-- toc -->

- [Why Colab?](#why-colab)
- [The five tutorials](#the-five-tutorials)
  - [01 — Engine API quickstart (mocked)](#01--engine-api-quickstart-mocked)
  - [02 — Groq cloud inference (live, free tier)](#02--groq-cloud-inference-live-free-tier)
  - [03 — Build your own corpus](#03--build-your-own-corpus)
  - [04 — MCP server from a Python client](#04--mcp-server-from-a-python-client)
  - [05 — Domain presets showcase](#05--domain-presets-showcase)
- [Running locally instead of Colab](#running-locally-instead-of-colab)
- [Common gotchas](#common-gotchas)

<!-- /toc -->

---

## Why Colab?

Colab works for tutorials because:

- **No local install friction** — click, run.
- **GPUs available** on the free tier (T4) for users who want to try the
  pipeline with larger models.
- **File upload / Drive integration** is smooth for bring-your-own-PDFs
  scenarios.
- Every cell output is captured, so tutorials stay reproducible.

What Colab **can't** do:

- **No Docker daemon** → can't run SearXNG or Ollama the usual way.
- **No systemd / long-lived background services** that outlive a cell.
- **Free-tier disconnects** after ~90 min idle or ~12 h total.

The tutorials work around these limits by:
- Mocking the LLM for the API walkthrough (Tutorial 01).
- Using a free hosted inference endpoint (Groq) for live runs (Tutorials 02, 03, 05).
- Running the MCP server in-process via `asyncio` (Tutorial 04).

---

## The five tutorials

### 01 — Engine API quickstart (mocked)

File: [`01_engine_api_quickstart.ipynb`](01_engine_api_quickstart.ipynb)

No API key required. Walks through:

1. `pip install` the engine's dependencies from the repo.
2. Invoke `build_graph()` with a stubbed LLM that returns canned
   responses — so the pipeline runs without touching any network.
3. Inspect every node's output: `state["question_class"]`,
   `state["subqueries"]`, `state["evidence"]`, `state["answer"]`,
   `state["claims"]`, `state["trace"]`.
4. Show the `run_query` helper and what a finished `RunResult` looks like.
5. Switch the domain preset to `medical` and see the prompt change.

**Good starting point** for anyone who wants to understand the engine's
internals without running real inference. ~2 minutes to finish.

### 02 — Groq cloud inference (live, free tier)

File: [`02_groq_cloud_inference.ipynb`](02_groq_cloud_inference.ipynb)

Requires: a free Groq API key (https://console.groq.com — generous free
tier, no credit card).

Walks through:

1. Paste your Groq API key into a Colab secret.
2. Point `OPENAI_BASE_URL` at `https://api.groq.com/openai/v1`.
3. Pick a fast model (`llama-3.3-70b-versatile` or `llama-3.1-8b-instant`).
4. Run a real multi-hop question end-to-end through the engine.
5. Inspect the trace, sources, and verified claims.

**When to use:** you want to see the engine's real output quality on
larger-than-laptop models without setting up vLLM. ~60 seconds per query.

### 03 — Build your own corpus

File: [`03_build_your_own_corpus.ipynb`](03_build_your_own_corpus.ipynb)

Walks through:

1. Upload 3–5 PDFs via Colab's file uploader (drag-and-drop).
2. Build a `CorpusIndex` from the uploaded files.
3. Save the index to Google Drive for reuse.
4. Query the corpus directly via `CorpusIndex.query()`.
5. Hook the corpus into the engine via `LOCAL_CORPUS_PATH` + domain
   preset `personal_docs`.
6. Ask the agent a question that should answer from your docs.

**When to use:** you want to ground the agent on your own papers,
reports, or notes. ~5 minutes including upload.

### 04 — MCP server from a Python client

File: [`04_mcp_server_from_python.ipynb`](04_mcp_server_from_python.ipynb)

Walks through:

1. Install the `mcp` SDK.
2. Start the engine's MCP server in a background asyncio task.
3. Connect to it as an MCP client and list available tools.
4. Call `research(question, domain, memory)` from the client.
5. Call `reset_memory()` + `memory_count()`.
6. Show how the same server would be registered in Claude Desktop.

**When to use:** you're building another agent (Claude Code, Cursor,
custom) that wants to call the engine as an MCP tool. ~3 minutes.

### 05 — Domain presets showcase

File: [`05_domain_presets_showcase.ipynb`](05_domain_presets_showcase.ipynb)

Walks through:

1. Load each of the 6 shipped domain presets.
2. Print the prompt deltas, verification strictness, and search biases.
3. Run the *same question* ("What's the evidence on omega-3 for
   cardiovascular health?") through `general`, `medical`, and `papers`
   presets — observe the structural differences in the answers.
4. Show how a custom preset is written in ~10 lines of YAML.

**When to use:** you want to understand which preset fits your domain
and how to write your own. ~4 minutes.

---

## Running locally instead of Colab

Every tutorial also runs locally — the Colab-specific steps
(`google.colab.files.upload`, Drive mounts) have commented-out local
equivalents in each notebook. If you have:

- Ollama + `gemma3:4b` installed, skip Groq and set
  `OPENAI_BASE_URL=http://localhost:11434/v1`, `OPENAI_API_KEY=ollama`.
- Docker running, start SearXNG via
  `(cd scripts/searxng && docker compose up -d)` and you get real web
  search. Without SearXNG, Tutorial 02 is still useful via Groq + the
  engine's own pipeline.

See `engine/README.md` + `docs/architecture.md` for the full local
setup flow.

---

## Common gotchas

| symptom | fix |
|---|---|
| `ModuleNotFoundError: engine` | The first cell installs from GitHub — re-run it, and add the repo path to `sys.path` (the notebook does this). |
| Groq 401 | Double-check the API key is pasted into Colab's secret manager, not into a code cell. |
| Corpus index mismatch | The index file format is version-tagged. If you built the index on an older engine version, rebuild. |
| MCP client hangs | Tutorial 04 uses `asyncio.wait_for` with a 30 s timeout; bump it if your inference backend is slow. |
| Colab disconnects mid-tutorial | Save the index to Drive (Tutorial 03 shows how); reconnecting restores your work. |

---

## Contributing a tutorial

If you write a notebook worth sharing, open a PR. Rules:

1. Runs end-to-end on Colab free tier within 10 minutes.
2. No API key required OR uses a service with a real free tier (not
   "credit card required").
3. Explains **why** each step is necessary, not just what.
4. All cell outputs cleared before commit (the reader regenerates them).
5. First cell links back to this README.

See `CONTRIBUTING.md` for the general PR process.
