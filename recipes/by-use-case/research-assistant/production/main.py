"""Research assistant — production tier with adaptive verification (Wave 2 Tier 2).

Extends the beginner pipeline with four 2026-SOTA techniques, wired into
a LangGraph with conditional edges so compute scales with question
difficulty:

  plan (+ HyDE) → search → retrieve → synthesize → verify (CoVe)
        │                                              │
        │                                              ▼
        │                                   verified? ──yes──▶ (optional) consistency ──▶ END
        │                                              │
        │                                              no
        │                                              │
        └──── iterate (re-search failed claims) ───────┘   (bounded by MAX_ITERATIONS)

References:
  - HyDE — Hypothetical Document Embeddings (Gao et al. 2023).
  - CoVe — Chain-of-Verification (Dhuliawala et al. 2023; MiroThinker-H1 2026).
  - ITER-RETGEN — iterative retrieval-generation (Shao et al. 2023).
  - Self-consistency — Wang et al. 2022 + scaling studies 2024-2026.

Same env-var contract as the beginner tier (OPENAI_BASE_URL, MODEL_*,
SEARXNG_URL, EMBED_MODEL). Additional knobs:
  ENABLE_HYDE            0|1    (default 1; auto-gated below on numeric queries)
  ENABLE_VERIFY          0|1    (default 1)
  MAX_ITERATIONS         int    (default 2)
  ENABLE_CONSISTENCY     0|1    (default 0; turn on for hard/ambiguous questions)
  CONSISTENCY_SAMPLES    int    (default 3)
"""

import os
import re
import sys
from concurrent.futures import ThreadPoolExecutor
from pathlib import Path
from typing import TypedDict

sys.path.insert(0, str(Path(__file__).resolve().parents[5]))

import requests  # noqa: E402
from core.rag import HybridRetriever  # noqa: E402
from langgraph.graph import END, StateGraph  # noqa: E402
from openai import OpenAI  # noqa: E402

ENV = os.environ.get
MODEL_PLANNER = ENV("MODEL_PLANNER", "gpt-5-nano")
MODEL_SEARCHER = ENV("MODEL_SEARCHER", "gpt-5-mini")
MODEL_SYNTHESIZER = ENV("MODEL_SYNTHESIZER", "gpt-5-mini")
MODEL_VERIFIER = ENV("MODEL_VERIFIER", MODEL_PLANNER)
NUM_SUBQUERIES = int(ENV("NUM_SUBQUERIES", "3"))
NUM_RESULTS_PER_QUERY = int(ENV("NUM_RESULTS_PER_QUERY", "5"))
TOP_K_EVIDENCE = int(ENV("TOP_K_EVIDENCE", "8"))
SEARXNG_URL = ENV("SEARXNG_URL", "http://localhost:8888")
ENABLE_HYDE = ENV("ENABLE_HYDE", "1") == "1"
ENABLE_VERIFY = ENV("ENABLE_VERIFY", "1") == "1"
MAX_ITERATIONS = int(ENV("MAX_ITERATIONS", "2"))
ENABLE_CONSISTENCY = ENV("ENABLE_CONSISTENCY", "0") == "1"
CONSISTENCY_SAMPLES = int(ENV("CONSISTENCY_SAMPLES", "3"))

# HyDE hurts numeric/exact queries; skip when the question looks factoid.
_NUMERIC_RE = re.compile(r"\b\d[\d,\.]*\b|\bhow many\b|\bwhen (was|did)\b|\bwhich year\b", re.IGNORECASE)
_CITE_RE = re.compile(r"\[(\d+)\]")


class State(TypedDict, total=False):
    question: str
    subqueries: list[str]
    evidence: list[dict]
    answer: str
    claims: list[dict]  # [{text, verified: bool, needs: str}]
    unverified: list[str]
    iterations: int


def _llm() -> OpenAI:
    return OpenAI(api_key=ENV("OPENAI_API_KEY", "ollama"), base_url=ENV("OPENAI_BASE_URL"))


def _chat(model: str, prompt: str, temperature: float = 0.0) -> str:
    resp = _llm().chat.completions.create(
        model=model, messages=[{"role": "user", "content": prompt}], temperature=temperature
    )
    return resp.choices[0].message.content or ""


def _searxng(query: str, n: int = NUM_RESULTS_PER_QUERY) -> list[dict]:
    r = requests.get(f"{SEARXNG_URL}/search", params={"q": query, "format": "json"}, timeout=20)
    r.raise_for_status()
    return [{"url": h.get("url", ""), "title": h.get("title", ""), "snippet": h.get("content", "")}
            for h in (r.json().get("results") or [])[:n]]


# ── Nodes ──────────────────────────────────────────────────────────────

def _plan(state: State) -> dict:
    """Decompose into sub-queries; optionally HyDE-rewrite each (unless numeric)."""
    prompt = (f"Break this research question into exactly {NUM_SUBQUERIES} focused sub-queries. "
              f"One per line, no numbering.\n\nQuestion: {state['question']}")
    subs = [l.strip(" -•*") for l in _chat(MODEL_PLANNER, prompt).splitlines() if l.strip()][:NUM_SUBQUERIES]
    if ENABLE_HYDE and not _NUMERIC_RE.search(state["question"]):
        subs = [_hyde_expand(s) for s in subs]
    return {"subqueries": subs, "iterations": state.get("iterations", 0)}


def _hyde_expand(sub: str) -> str:
    """Generate a hypothetical answer passage; use its text as the retrieval query."""
    hyde = _chat(MODEL_PLANNER,
                 f"Write one concise factual paragraph answering: {sub}\n"
                 f"Respond with ONLY the paragraph, no preamble.")
    return f"{sub}\n\n{hyde.strip()}"


def _search_one(sub: str) -> list[dict]:
    hits = _searxng(sub)
    if not hits:
        return []
    sources = "\n".join(f"[{i+1}] {h['title']} — {h['snippet']}  (url: {h['url']})" for i, h in enumerate(hits))
    summary = _chat(MODEL_SEARCHER,
                    f"Summarize these sources factually in 3-5 sentences with inline [1], [2] citations. "
                    f"Only use the information provided.\n\nSub-query: {sub}\n\nSources:\n{sources}")
    return [{"url": h["url"], "title": h["title"], "text": summary} for h in hits]


def _search(state: State) -> dict:
    """Fan-out parallel search; dedupe evidence by URL; append to existing evidence on iteration."""
    subs = state.get("unverified") or state["subqueries"]
    with ThreadPoolExecutor(max_workers=max(len(subs), 1)) as pool:
        new_items = [e for batch in pool.map(_search_one, subs) for e in batch]
    existing = state.get("evidence", [])
    seen = {e["url"] for e in existing}
    return {"evidence": existing + [e for e in new_items if e["url"] and e["url"] not in seen and not seen.add(e["url"])]}


def _retrieve(state: State) -> dict:
    ev = state["evidence"]
    if len(ev) <= TOP_K_EVIDENCE:
        return {"evidence": ev}
    r = HybridRetriever()
    r.add([e["text"] for e in ev])
    top = r.retrieve(state["question"], k=TOP_K_EVIDENCE)
    by_text = {e["text"]: e for e in ev}
    return {"evidence": [by_text[text] for text, _ in top if text in by_text]}


def _synthesize_once(state: State) -> str:
    bullets = "\n".join(f"[{i+1}] {e['text']}  (src: {e['url']})" for i, e in enumerate(state["evidence"]))
    prompt = (f"Answer using the evidence. Cite sources inline as [1], [2], etc. Be concise and factual. "
              f"If an aspect is not supported by the evidence, say so explicitly.\n\n"
              f"Question: {state['question']}\n\nEvidence:\n{bullets}")
    return _chat(MODEL_SYNTHESIZER, prompt)


def _grounding_score(answer: str, evidence: list[dict]) -> float:
    """Ranking signal for self-consistency: blends validity ratio with coverage.

    Equal validity ratios are broken by the number of valid citations — a
    richer cited answer ranks higher than a sparsely cited one when both
    are 100% valid. This is not a validity metric (eval/scorer.py has one
    of those); it's a comparator for picking the best of N candidates.
    """
    refs = {int(m) for m in _CITE_RE.findall(answer)}
    if not refs:
        return 0.0
    valid = sum(1 for r in refs if 1 <= r <= len(evidence))
    return (valid / len(refs)) * (valid ** 0.5)


def _synthesize(state: State) -> dict:
    """Synthesize once, or N times with self-consistency pick-by-grounding when enabled."""
    if not ENABLE_CONSISTENCY:
        return {"answer": _synthesize_once(state)}
    candidates = [_synthesize_once(state) for _ in range(CONSISTENCY_SAMPLES)]
    best = max(candidates, key=lambda a: _grounding_score(a, state["evidence"]))
    return {"answer": best}


def _verify(state: State) -> dict:
    """CoVe: decompose answer into claims; verify each; flag unverified."""
    if not ENABLE_VERIFY:
        return {"claims": [], "unverified": []}
    bullets = "\n".join(f"[{i+1}] {e['text']}" for i, e in enumerate(state["evidence"]))
    prompt = (f"You are verifying a candidate answer. List each standalone factual claim on its own line "
              f"as `CLAIM: <text>`. Then for each claim, output `VERIFIED: yes` or `VERIFIED: no` based "
              f"STRICTLY on whether the evidence below supports it.\n\n"
              f"Answer:\n{state['answer']}\n\nEvidence:\n{bullets}")
    raw = _chat(MODEL_VERIFIER, prompt)
    claims: list[dict] = []
    current: dict | None = None
    for line in raw.splitlines():
        line = line.strip()
        if line.upper().startswith("CLAIM:"):
            current = {"text": line.split(":", 1)[1].strip(), "verified": False}
            claims.append(current)
        elif line.upper().startswith("VERIFIED:") and current is not None:
            current["verified"] = "yes" in line.lower()
            current = None
    unverified = [c["text"] for c in claims if not c["verified"]]
    return {"claims": claims, "unverified": unverified, "iterations": state.get("iterations", 0) + 1}


def _after_verify(state: State) -> str:
    """Conditional edge: iterate on unverified claims (bounded), else end."""
    if ENABLE_VERIFY and state.get("unverified") and state.get("iterations", 0) < MAX_ITERATIONS:
        return "search"
    return END


# ── Graph ──────────────────────────────────────────────────────────────

def build_graph():
    g = StateGraph(State)
    for n, f in [("plan", _plan), ("search", _search), ("retrieve", _retrieve),
                 ("synthesize", _synthesize), ("verify", _verify)]:
        g.add_node(n, f)
    g.set_entry_point("plan")
    for a, b in [("plan", "search"), ("search", "retrieve"), ("retrieve", "synthesize"),
                 ("synthesize", "verify")]:
        g.add_edge(a, b)
    g.add_conditional_edges("verify", _after_verify, {"search": "search", END: END})
    return g.compile()


if __name__ == "__main__":
    q = " ".join(sys.argv[1:]) or "What is Anthropic's contextual retrieval and why does it reduce retrieval failures?"
    print(f"Q: {q}")
    result = build_graph().invoke({"question": q, "iterations": 0})
    print(f"\nA: {result['answer']}")
    if result.get("claims"):
        print(f"\nVerified: {sum(1 for c in result['claims'] if c['verified'])}/{len(result['claims'])} claims")
        if result.get("unverified"):
            print(f"Unverified after {result.get('iterations', 0)} iteration(s): {len(result['unverified'])}")
