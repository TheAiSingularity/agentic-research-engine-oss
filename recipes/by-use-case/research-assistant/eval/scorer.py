"""Scorer for research-assistant — factuality + citation accuracy + cost/latency.

Usage: python scorer.py [dataset.jsonl]

Metrics:
    factuality_mean            — LLM-as-judge rating vs gold (0 / 0.5 / 1)
    citation_precision_mean    — proportion of required domains appearing in URLs
    citation_accuracy_mean     — proportion of [N] references that resolve to
                                 real evidence items (catches hallucinated refs)
    latency_mean_s             — wall-clock seconds per question
    tokens_est_mean            — rough token count over evidence + answer text

Requires OPENAI_API_KEY for the judge (LLM-as-judge factuality only). The
agent itself uses whatever backend is configured via OPENAI_BASE_URL.
"""

from __future__ import annotations

import json
import os
import re
import sys
import time
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[5]
sys.path.insert(0, str(REPO_ROOT))
sys.path.insert(0, str(Path(__file__).parent.parent / "beginner"))

from main import build_graph  # noqa: E402
from openai import OpenAI  # noqa: E402

JUDGE_MODEL = os.getenv("JUDGE_MODEL", "gpt-5-mini")
URL_RE = re.compile(r"https?://[^\s)]+")
CITE_RE = re.compile(r"\[(\d+)\]")


def _judge_factuality(client: OpenAI, question: str, gold: str, answer: str) -> float:
    """LLM-as-judge. Returns 0.0 / 0.5 / 1.0 for incorrect / partial / correct."""
    prompt = (
        f"Rate the candidate answer against the gold answer for factual accuracy. "
        f"Reply with ONLY a number: 0 (incorrect), 0.5 (partially correct), or 1 (correct).\n\n"
        f"Question: {question}\nGold: {gold}\nCandidate: {answer}"
    )
    resp = client.chat.completions.create(
        model=JUDGE_MODEL, messages=[{"role": "user", "content": prompt}]
    )
    text = (resp.choices[0].message.content or "0").strip()
    try:
        return max(0.0, min(1.0, float(text.split()[0])))
    except (ValueError, IndexError):
        return 0.0


def _citation_precision(answer: str, must_cite_any: list[str]) -> float:
    """Proportion of `must_cite_any` domains that appear in the answer's URLs."""
    if not must_cite_any:
        return 1.0
    urls = URL_RE.findall(answer)
    hits = sum(1 for needle in must_cite_any if any(needle in u for u in urls))
    return hits / max(1, len(must_cite_any))


def _citation_accuracy(answer: str, evidence: list[dict]) -> float:
    """Fraction of `[N]` refs in the answer that point at a real evidence row.

    Catches hallucinated citations (e.g., `[7]` when only 3 evidence items
    exist) that the LLM occasionally inserts. 1.0 means every ref is grounded.
    """
    refs = {int(m) for m in CITE_RE.findall(answer)}
    if not refs:
        return 1.0  # no claims to ground
    valid = sum(1 for r in refs if 1 <= r <= len(evidence))
    return valid / len(refs)


def _estimate_tokens(text: str) -> int:
    """Cheap tokens-per-text estimate: ~1 token per 4 characters (English)."""
    return max(1, len(text) // 4)


def score_dataset(path: Path) -> dict:
    graph = build_graph()
    judge = OpenAI(api_key=os.environ["OPENAI_API_KEY"])
    factuality: list[float] = []
    cit_prec: list[float] = []
    cit_acc: list[float] = []
    latency: list[float] = []
    tokens: list[int] = []
    for line in path.read_text().splitlines():
        if not line.strip():
            continue
        row = json.loads(line)
        t0 = time.time()
        result = graph.invoke(
            {"question": row["question"], "subqueries": [], "evidence": [], "answer": ""}
        )
        latency.append(time.time() - t0)
        answer = result["answer"]
        evidence = result.get("evidence", [])
        tokens.append(sum(_estimate_tokens(e.get("text", "")) for e in evidence) + _estimate_tokens(answer))
        factuality.append(_judge_factuality(judge, row["question"], row["gold_answer"], answer))
        cit_prec.append(_citation_precision(answer, row.get("must_cite_any", [])))
        cit_acc.append(_citation_accuracy(answer, evidence))
        print(
            f"  {row['id']}: "
            f"fact={factuality[-1]:.2f}  cprec={cit_prec[-1]:.2f}  "
            f"cacc={cit_acc[-1]:.2f}  {latency[-1]:.1f}s  ~{tokens[-1]}tok"
        )
    n = len(factuality) or 1
    return {
        "n": len(factuality),
        "factuality_mean": sum(factuality) / n,
        "citation_precision_mean": sum(cit_prec) / n,
        "citation_accuracy_mean": sum(cit_acc) / n,
        "latency_mean_s": sum(latency) / n,
        "tokens_est_mean": sum(tokens) / n,
    }


if __name__ == "__main__":
    dataset = Path(sys.argv[1]) if len(sys.argv) > 1 else Path(__file__).parent / "dataset.jsonl"
    print(f"Scoring {dataset} …")
    scores = score_dataset(dataset)
    print(f"\nAggregate over {scores['n']} examples:")
    print(f"  factuality_mean           = {scores['factuality_mean']:.3f}")
    print(f"  citation_precision_mean   = {scores['citation_precision_mean']:.3f}")
    print(f"  citation_accuracy_mean    = {scores['citation_accuracy_mean']:.3f}")
    print(f"  latency_mean_s            = {scores['latency_mean_s']:.2f}")
    print(f"  tokens_est_mean           = {scores['tokens_est_mean']:.0f}")
