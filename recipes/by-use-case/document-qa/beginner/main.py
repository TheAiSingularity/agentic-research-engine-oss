"""document-qa beginner — answer questions over your own documents.

The natural companion to Wave 5's `CorpusIndex`. Drop a directory of PDFs /
markdown / text / HTML at `DOCS_DIR`, the first run indexes it, and every
subsequent question is answered with cited `corpus://` source refs.

Pipeline (4 nodes — no web-reach, no iteration, no router):

    load_corpus → retrieve → (optional stream) synthesize → verify
                     │
                     ▼
         HybridRetriever (BM25 + dense + RRF) over the index
                     │
                     ▼
              MODEL_SYNTHESIZER answers with [N] citations; if the
              evidence doesn't cover the question, it says so

Positioned as the third flagship recipe after research-assistant and
trading-copilot. Proves the `core.rag.CorpusIndex` API works end-to-end
for a bring-your-own-documents use case (no SearXNG, no trafilatura on
the hot path — corpus chunks are full text already).

Env vars (defaults shown):
  DOCS_DIR              ""     directory of PDFs / md / txt / html to index
                                (required on first run unless CORPUS_PATH
                                 points at a prebuilt index)
  CORPUS_PATH           ""     path to a prebuilt index from scripts/index_corpus.py;
                                when set, skips the index-build step
  OPENAI_BASE_URL       …      any OpenAI-compatible endpoint (Ollama, vLLM, cloud)
  OPENAI_API_KEY        ollama
  MODEL_SYNTHESIZER     gemma4:e2b     answer generator
  MODEL_VERIFIER        == synth       CoVe claim checker
  EMBED_MODEL           nomic-embed-text
  TOP_K                 5             retrieved chunks per question
  ENABLE_VERIFY         1             CoVe claim check after synthesize
  ENABLE_STREAM         1             stream synth tokens to stdout
"""

from __future__ import annotations

import os
import re
import sys
import time
from pathlib import Path
from typing import TypedDict

sys.path.insert(0, str(Path(__file__).resolve().parents[4]))

from core.rag import CorpusIndex  # noqa: E402
from langgraph.graph import END, StateGraph  # noqa: E402
from openai import OpenAI  # noqa: E402

ENV = os.environ.get
DOCS_DIR = ENV("DOCS_DIR", "")
CORPUS_PATH = ENV("CORPUS_PATH", "")
MODEL_SYNTHESIZER = ENV("MODEL_SYNTHESIZER", "gemma4:e2b")
MODEL_VERIFIER = ENV("MODEL_VERIFIER", MODEL_SYNTHESIZER)
TOP_K = int(ENV("TOP_K", "5"))
ENABLE_VERIFY = ENV("ENABLE_VERIFY", "1") == "1"
ENABLE_STREAM = ENV("ENABLE_STREAM", "1") == "1"


class State(TypedDict, total=False):
    question: str
    corpus: object          # CorpusIndex at runtime; `object` avoids
                            # TypedDict forward-ref eval in LangGraph's ns
    hits: list[dict]        # retrieved chunks shaped for the prompt
    answer: str
    claims: list[dict]
    verified_count: int


# ── LLM plumbing ──────────────────────────────────────────────────────

def _llm() -> OpenAI:
    return OpenAI(api_key=ENV("OPENAI_API_KEY", "ollama"), base_url=ENV("OPENAI_BASE_URL"))


def _chat(model: str, prompt: str) -> str:
    resp = _llm().chat.completions.create(
        model=model, messages=[{"role": "user", "content": prompt}], temperature=0.0
    )
    return resp.choices[0].message.content or ""


def _chat_stream(model: str, prompt: str) -> str:
    """Token-stream to stdout; fall back to batched on backend error."""
    try:
        stream = _llm().chat.completions.create(
            model=model, messages=[{"role": "user", "content": prompt}],
            temperature=0.0, stream=True,
        )
    except Exception:
        return _chat(model, prompt)
    pieces: list[str] = []
    try:
        for chunk in stream:
            choices = getattr(chunk, "choices", None) or []
            if not choices:
                continue
            delta = getattr(choices[0], "delta", None)
            tok = (getattr(delta, "content", None) or "") if delta else ""
            if tok:
                pieces.append(tok)
                sys.stdout.write(tok)
                sys.stdout.flush()
    except Exception:
        pass
    sys.stdout.write("\n")
    sys.stdout.flush()
    return "".join(pieces)


# ── Nodes ─────────────────────────────────────────────────────────────

def _load_corpus(state: State) -> dict:
    """Load a prebuilt index from CORPUS_PATH, or build one from DOCS_DIR."""
    if CORPUS_PATH:
        idx = CorpusIndex.load(CORPUS_PATH)
        print(f"[corpus] loaded {len(idx.chunks)} chunks from {CORPUS_PATH}", file=sys.stderr)
        return {"corpus": idx}
    if not DOCS_DIR:
        raise RuntimeError("Set DOCS_DIR to a directory of documents, or CORPUS_PATH to a prebuilt index.")
    t0 = time.monotonic()
    idx = CorpusIndex.build(DOCS_DIR)
    n_sources = len({c.source for c in idx.chunks})
    print(f"[corpus] built {len(idx.chunks)} chunks from {n_sources} sources in {time.monotonic()-t0:.1f}s",
          file=sys.stderr)
    return {"corpus": idx}


def _retrieve(state: State) -> dict:
    """Hybrid top-K against the corpus; shape as prompt-ready evidence items."""
    idx = state["corpus"]
    raw_hits = idx.query(state["question"], k=TOP_K)
    hits: list[dict] = []
    for chunk, score in raw_hits:
        loc = f"corpus://{chunk.source}"
        if chunk.page is not None:
            loc += f"#p{chunk.page}"
        loc += f"#c{chunk.chunk_idx}"
        hits.append({"url": loc, "text": chunk.text, "score": float(score)})
    return {"hits": hits}


def _synthesize(state: State) -> dict:
    """Generate a cited answer from the retrieved chunks."""
    hits = state.get("hits") or []
    if not hits:
        return {"answer": "No relevant chunks were retrieved from the corpus."}
    bullets = "\n".join(f"[{i+1}] {h['text']}  (src: {h['url']})" for i, h in enumerate(hits))
    prompt = (
        "Answer the question using ONLY the evidence. Rules:\n"
        "  1. Cite every factual claim inline as [1], [2], etc.\n"
        "  2. If the evidence FULLY answers the question: answer concisely.\n"
        "  3. If the evidence partially answers: answer supported parts, "
        "then name the aspects NOT supported by the evidence.\n"
        "  4. If the evidence is UNRELATED: reply exactly "
        "\"The provided evidence does not answer this question.\" — nothing else.\n"
        "  5. Never invent facts or substitute a related topic.\n\n"
        f"Question: {state['question']}\n\nEvidence:\n{bullets}"
    )
    answer = _chat_stream(MODEL_SYNTHESIZER, prompt) if ENABLE_STREAM else _chat(MODEL_SYNTHESIZER, prompt)
    return {"answer": answer}


def _verify(state: State) -> dict:
    """CoVe — decompose the answer into claims and check each vs evidence."""
    if not ENABLE_VERIFY or not state.get("answer"):
        return {"claims": [], "verified_count": 0}
    hits = state.get("hits") or []
    bullets = "\n".join(f"[{i+1}] {h['text']}" for i, h in enumerate(hits))
    prompt = (
        "List each standalone factual claim in the answer on its own line as "
        "`CLAIM: <text>`. Then for each claim output `VERIFIED: yes|no` based "
        "STRICTLY on whether the evidence supports it.\n\n"
        f"Answer:\n{state['answer']}\n\nEvidence:\n{bullets}"
    )
    raw = _chat(MODEL_VERIFIER, prompt)
    claims: list[dict] = []
    current: dict | None = None
    for line in raw.splitlines():
        s = line.strip()
        if s.upper().startswith("CLAIM:"):
            current = {"text": s.split(":", 1)[1].strip(), "verified": False}
            claims.append(current)
        elif s.upper().startswith("VERIFIED:") and current is not None:
            current["verified"] = "yes" in s.lower()
            current = None
    return {"claims": claims, "verified_count": sum(1 for c in claims if c["verified"])}


# ── Graph ─────────────────────────────────────────────────────────────

def build_graph():
    g = StateGraph(State)
    for n, f in [("load_corpus", _load_corpus), ("retrieve", _retrieve),
                 ("synthesize", _synthesize), ("verify", _verify)]:
        g.add_node(n, f)
    g.set_entry_point("load_corpus")
    for a, b in [("load_corpus", "retrieve"), ("retrieve", "synthesize"), ("synthesize", "verify")]:
        g.add_edge(a, b)
    g.add_edge("verify", END)
    return g.compile()


if __name__ == "__main__":
    q = " ".join(sys.argv[1:]) or "What is this corpus about?"
    print(f"Q: {q}\n")
    result = build_graph().invoke({"question": q})
    # Streaming already printed the answer live; in batched mode print it explicitly.
    if not ENABLE_STREAM:
        print(f"A: {result['answer']}")
    hits = result.get("hits") or []
    if hits:
        print(f"\nCited sources:")
        for i, h in enumerate(hits, 1):
            print(f"  [{i}] {h['url']}")
    claims = result.get("claims") or []
    if claims:
        v = sum(1 for c in claims if c["verified"])
        print(f"\nVerified: {v}/{len(claims)} claims")
