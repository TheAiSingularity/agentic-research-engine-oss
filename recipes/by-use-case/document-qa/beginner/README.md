# document-qa / beginner

**Answer questions over your own documents.** Drop a directory of
PDFs / markdown / text / HTML at `DOCS_DIR`, the first run indexes it,
every subsequent question is answered with cited `corpus://…` source
refs. Pure local: no web search, no SearXNG, no paid APIs.

## Pipeline

```
load_corpus → retrieve (hybrid BM25 + dense + RRF) → synthesize (streaming) → verify (CoVe)
```

Four nodes. No router, no iteration, no compressor — the corpus is
bounded, those pay off for open-web research. See [`techniques.md`](techniques.md)
for why.

## Run

### Mac local (Ollama + gemma4:e2b + nomic-embed-text)

```bash
bash ../../../../scripts/setup-local-mac.sh   # if not already set up
export OPENAI_BASE_URL=http://localhost:11434/v1
export OPENAI_API_KEY=ollama
export MODEL_SYNTHESIZER=gemma4:e2b
export MODEL_VERIFIER=gemma4:e2b
export EMBED_MODEL=nomic-embed-text

make install
make smoke         # uses the tiny fixture corpus shipped with the recipe

# or your own docs:
DOCS_DIR=~/papers make run Q="What is retrieval-augmented generation?"
```

### GPU VM (vLLM or SGLang + Qwen3.6-35B-A3B)

```bash
bash ../../../../scripts/setup-vm-gpu.sh --engine sglang --spec-dec \
  --model Qwen/Qwen3.6-35B-A3B
# exports OPENAI_BASE_URL etc.
DOCS_DIR=~/papers make run Q="What is retrieval-augmented generation?"
```

### Cloud (OpenAI)

```bash
export OPENAI_API_KEY=sk-...
export MODEL_SYNTHESIZER=gpt-5-mini
export EMBED_MODEL=text-embedding-3-small
DOCS_DIR=~/papers make run Q="…"
```

## Prebuilt indexes

Building the index on every run is fine for small corpora. For larger
ones (hundreds of PDFs), build once with
[`scripts/index_corpus.py`](../../../../scripts/index_corpus.py) and
point `CORPUS_PATH` at the result:

```bash
OPENAI_BASE_URL=http://localhost:11434/v1 OPENAI_API_KEY=ollama \
EMBED_MODEL=nomic-embed-text \
python ../../../../scripts/index_corpus.py build ~/papers --out ~/papers.idx

export CORPUS_PATH=~/papers.idx
make run Q="…"
```

## Test

```bash
make test   # mocked; no API key, no network
```

## Env vars (defaults shown)

| Var | Default | Purpose |
|---|---|---|
| `DOCS_DIR` | `""` | Directory to index at startup |
| `CORPUS_PATH` | `""` | Prebuilt index (skips the build step) |
| `MODEL_SYNTHESIZER` | `gemma4:e2b` | Answer generator |
| `MODEL_VERIFIER` | `$MODEL_SYNTHESIZER` | CoVe claim checker |
| `TOP_K` | `5` | Retrieved chunks per question |
| `ENABLE_VERIFY` | `1` | CoVe claim check |
| `ENABLE_STREAM` | `1` | Stream tokens to stdout |

## What this recipe proves

The Wave 5 `CorpusIndex` API works end-to-end as a standalone recipe
without pulling in any of the Wave 4 web-fetch machinery. That's the
"core/rag graduation" test DEC-004 commits to — if `core/rag` is
genuinely reusable, a bring-your-own-docs recipe should be ~200 LOC and
reuse everything without duplication. It is, and it does.

## Not shipped here (by design)

- No cross-encoder rerank (see research-assistant/production for that).
- No multi-corpus fusion.
- No uploads or UI — this is a CLI recipe. Adapt the graph to your
  web framework of choice if you want a browser UI.
