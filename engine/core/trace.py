"""engine.core.trace — W4.3 observability.

Per-call trace buffer + node-level merge + CLI summary printer. Moved here
from the monolithic `recipes/.../production/main.py` so all three interfaces
(CLI, TUI, Web GUI) can render the same data without copy-paste.

Design note: `_TRACE_BUFFER` is a module-level list appended to by
`models._chat` and `models._chat_stream`. Nodes drain it via
`_merge_trace(state, node_name)` and fold the entries into `state["trace"]`.
This pattern works under LangGraph's sequential execution and survives
ThreadPoolExecutor parallelism (CPython's GIL makes list.append atomic).
"""

from __future__ import annotations

import os


ENV = os.environ.get
ENABLE_TRACE = ENV("ENABLE_TRACE", "1") == "1"

# Module-level buffer: every LLM call appends; nodes drain + tag.
_TRACE_BUFFER: list[dict] = []


def _drain_trace(node: str) -> list[dict]:
    """Tag every buffered entry with `node`, return them, clear the buffer."""
    if not _TRACE_BUFFER:
        return []
    entries = [{"node": node, **e} for e in _TRACE_BUFFER]
    _TRACE_BUFFER.clear()
    return entries


def _merge_trace(state, node: str, extras: list[dict] | None = None) -> list[dict]:
    """Return `state["trace"]` extended with this node's drained entries + extras."""
    delta = _drain_trace(node)
    if extras:
        delta.extend({"node": node, **e} for e in extras)
    return state.get("trace", []) + delta


def _print_trace_summary(trace: list[dict]) -> None:
    """One-pass summary: per-node and per-model totals. Printed to stdout."""
    if not trace:
        return
    by_node: dict[str, dict] = {}
    by_model: dict[str, dict] = {}
    total_latency = 0.0
    total_tokens = 0
    for e in trace:
        node = e.get("node", "?")
        model = e.get("model", "?")
        latency = float(e.get("latency_s", 0) or 0)
        tokens = int(e.get("tokens_est", 0) or 0)
        total_latency += latency
        total_tokens += tokens
        for bucket, key in ((by_node, node), (by_model, model)):
            b = bucket.setdefault(key, {"calls": 0, "latency_s": 0.0, "tokens_est": 0})
            b["calls"] += 1
            b["latency_s"] += latency
            b["tokens_est"] += tokens

    print(f"\n── trace summary ({len(trace)} entries, {total_latency:.2f}s total, ~{total_tokens} tokens) ──")
    print("  by node:")
    for node, b in sorted(by_node.items(), key=lambda kv: -kv[1]["latency_s"]):
        print(f"    {node:12s}  calls={b['calls']:2d}  latency={b['latency_s']:6.2f}s  tokens~{b['tokens_est']}")
    print("  by model:")
    for model, b in sorted(by_model.items(), key=lambda kv: -kv[1]["latency_s"]):
        print(f"    {model:22s}  calls={b['calls']:2d}  latency={b['latency_s']:6.2f}s  tokens~{b['tokens_est']}")


__all__ = ["ENABLE_TRACE", "_TRACE_BUFFER", "_drain_trace", "_merge_trace", "_print_trace_summary"]
