"""engine.core.domains — YAML preset loader.

Each domain preset (`engine/domains/*.yaml`) is a declarative config that
nudges the pipeline for a specific research workflow without code changes:

  - search sources (SearXNG category filters, seed URLs, RSS feeds)
  - prompt deltas (appended to the synthesize prompt's rule block)
  - verification strictness (require-verified-claims floor)
  - default memory domain tag
  - default corpus path (for bring-your-own-docs presets)
  - specialist tools toggled on/off (e.g. pubmed_search)

Presets are applied by the interface layers before calling `build_graph()`.
Keeping them OUT of `pipeline.py` means we can add/remove/tune a domain
by editing a YAML file — no pipeline changes, no test churn.
"""

from __future__ import annotations

import os
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any

ENV = os.environ.get

DEFAULT_DOMAINS_DIR = Path(__file__).resolve().parents[1] / "domains"


@dataclass
class DomainPreset:
    """Loaded domain preset."""

    name: str
    description: str = ""
    # Search behavior
    searxng_categories: list[str] = field(default_factory=list)
    seed_queries: list[str] = field(default_factory=list)
    rss_feeds: list[str] = field(default_factory=list)
    # Prompt behavior
    synthesize_prompt_extra: str = ""
    # Verification behavior
    min_verified_ratio: float = 0.0   # reject answers with lower verified/total
    # Retrieval behavior
    corpus_path: str = ""              # if set, overrides LOCAL_CORPUS_PATH
    top_k_evidence: int | None = None
    # Specialized tools (future)
    tools_enabled: list[str] = field(default_factory=list)
    # Arbitrary passthrough
    extra: dict[str, Any] = field(default_factory=dict)


def _parse_simple_yaml(text: str) -> dict:
    """Tiny YAML reader for the preset format — no PyYAML dependency.

    Supports:
      key: scalar
      key: "quoted scalar"
      key:                          (opens a list)
        - list item
        - "quoted list item"
      key: [inline, list]
      key: |                        (literal block scalar — newlines preserved)
        multiple
        lines of text
      key: >                        (folded block scalar — newlines → spaces)
        multiple
        lines of text
    """
    data: dict = {}
    # Preserve indentation since block-scalars care about it.
    raw_lines = text.splitlines()
    i = 0
    n = len(raw_lines)
    current_list_key: str | None = None

    while i < n:
        raw = raw_lines[i]
        stripped = raw.strip()

        # Skip blank + full-line comments.
        if not stripped or stripped.startswith("#"):
            i += 1
            continue

        indent = len(raw) - len(raw.lstrip())
        content = stripped

        # List item under the last opened key.
        if content.startswith("- ") and current_list_key is not None:
            val = content[2:].strip()
            if val.startswith('"') and val.endswith('"'):
                val = val[1:-1]
            data.setdefault(current_list_key, []).append(val)
            i += 1
            continue

        if ":" not in content:
            i += 1
            continue

        k, _, v = content.partition(":")
        k = k.strip()
        v = v.strip()
        current_list_key = None

        # Block scalar — consume all subsequent lines that are indented
        # deeper than the key itself.
        if v in ("|", ">"):
            block_lines: list[str] = []
            i += 1
            while i < n:
                nl = raw_lines[i]
                nl_indent = len(nl) - len(nl.lstrip())
                if nl.strip() == "" or nl_indent > indent:
                    # Strip just the base indent (indent + 2 usual) off each line.
                    strip_n = indent + 2
                    block_lines.append(nl[strip_n:] if len(nl) >= strip_n else nl.lstrip())
                    i += 1
                else:
                    break
            if v == "|":
                data[k] = "\n".join(block_lines).rstrip("\n")
            else:  # ">"
                # Fold: blank lines become paragraph breaks, other newlines → space.
                joined: list[str] = []
                para: list[str] = []
                for bl in block_lines:
                    if bl.strip() == "":
                        if para:
                            joined.append(" ".join(para))
                            para = []
                    else:
                        para.append(bl.strip())
                if para:
                    joined.append(" ".join(para))
                data[k] = "\n\n".join(joined)
            continue

        if v == "":
            data[k] = []
            current_list_key = k
        elif v.startswith("[") and v.endswith("]"):
            inner = v[1:-1].strip()
            items = [s.strip().strip('"').strip("'") for s in inner.split(",")] if inner else []
            data[k] = items
        elif v.startswith('"') and v.endswith('"'):
            data[k] = v[1:-1]
        elif v.lower() in ("true", "false"):
            data[k] = v.lower() == "true"
        else:
            try:
                if "." in v:
                    data[k] = float(v)
                else:
                    data[k] = int(v)
            except ValueError:
                data[k] = v
        i += 1
    return data


def load(name: str, *, root: Path = DEFAULT_DOMAINS_DIR) -> DomainPreset:
    """Load a preset by name. Raises FileNotFoundError if missing."""
    path = root / f"{name}.yaml"
    if not path.exists():
        raise FileNotFoundError(f"domain preset {name!r} not found at {path}")
    data = _parse_simple_yaml(path.read_text())
    return DomainPreset(
        name=str(data.get("name", name)),
        description=str(data.get("description", "")),
        searxng_categories=list(data.get("searxng_categories", []) or []),
        seed_queries=list(data.get("seed_queries", []) or []),
        rss_feeds=list(data.get("rss_feeds", []) or []),
        synthesize_prompt_extra=str(data.get("synthesize_prompt_extra", "") or ""),
        min_verified_ratio=float(data.get("min_verified_ratio", 0.0) or 0.0),
        corpus_path=str(data.get("corpus_path", "") or ""),
        top_k_evidence=data.get("top_k_evidence"),
        tools_enabled=list(data.get("tools_enabled", []) or []),
        extra={k: v for k, v in data.items() if k not in {
            "name", "description", "searxng_categories", "seed_queries",
            "rss_feeds", "synthesize_prompt_extra", "min_verified_ratio",
            "corpus_path", "top_k_evidence", "tools_enabled",
        }},
    )


def list_names(*, root: Path = DEFAULT_DOMAINS_DIR) -> list[str]:
    """Return all preset names found under `root` sorted alphabetically."""
    if not root.exists():
        return []
    return sorted(p.stem for p in root.glob("*.yaml"))


def apply_preset(preset: DomainPreset) -> dict:
    """Translate a preset into env-var overrides the pipeline honors.

    Returns a dict of env-var -> str-value. Callers (interfaces) can
    inject this into `os.environ` before building the graph.
    """
    overrides: dict[str, str] = {}
    if preset.corpus_path:
        overrides["LOCAL_CORPUS_PATH"] = preset.corpus_path
    if preset.top_k_evidence is not None:
        overrides["TOP_K_EVIDENCE"] = str(preset.top_k_evidence)
    return overrides


__all__ = [
    "DEFAULT_DOMAINS_DIR",
    "DomainPreset",
    "load",
    "list_names",
    "apply_preset",
]
