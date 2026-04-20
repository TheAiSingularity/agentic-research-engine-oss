"""Mocked tests for engine.core.domains — YAML preset loader.

The parser is dependency-free (no PyYAML), so tests exercise its actual
implementation against both synthetic fixtures and the shipped preset files.
"""

from __future__ import annotations

import sys
import textwrap
from pathlib import Path

import pytest

REPO_ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(REPO_ROOT))

from engine.core.domains import (  # noqa: E402
    DEFAULT_DOMAINS_DIR,
    DomainPreset,
    apply_preset,
    list_names,
    load,
    _parse_simple_yaml,
)


# ── YAML parser ──────────────────────────────────────────────────────

def test_parse_simple_yaml_scalars():
    text = 'name: medical\ndescription: "Medical research"\nmin_verified_ratio: 0.75\n'
    data = _parse_simple_yaml(text)
    assert data["name"] == "medical"
    assert data["description"] == "Medical research"
    assert data["min_verified_ratio"] == 0.75


def test_parse_simple_yaml_list():
    text = textwrap.dedent("""\
        seed_queries:
          - "site:arxiv.org"
          - "site:semanticscholar.org"
    """)
    data = _parse_simple_yaml(text)
    assert data["seed_queries"] == ["site:arxiv.org", "site:semanticscholar.org"]


def test_parse_simple_yaml_inline_list():
    text = 'tools_enabled: [pubmed_search, cochrane]\n'
    data = _parse_simple_yaml(text)
    assert data["tools_enabled"] == ["pubmed_search", "cochrane"]


def test_parse_simple_yaml_booleans():
    text = "enabled: true\ndebug: false\n"
    data = _parse_simple_yaml(text)
    assert data["enabled"] is True
    assert data["debug"] is False


def test_parse_simple_yaml_ignores_comments():
    text = "# top comment\nname: x\n  # indented\n"
    data = _parse_simple_yaml(text)
    assert data == {"name": "x"}


# ── load() ──────────────────────────────────────────────────────────

def test_load_ships_all_six_builtin_presets():
    # After Phase 6 these MUST exist.
    names = list_names()
    assert set(names) == {"general", "medical", "papers", "financial", "stock_trading", "personal_docs"}


def test_load_general_preset_has_safe_defaults():
    preset = load("general")
    assert preset.name == "general"
    assert preset.searxng_categories == []
    assert preset.seed_queries == []
    assert preset.min_verified_ratio == 0.0
    assert preset.corpus_path == ""
    assert preset.tools_enabled == []


def test_load_medical_preset_has_strict_verify_and_pubmed_seed():
    preset = load("medical")
    assert preset.name == "medical"
    assert preset.min_verified_ratio == 0.75
    assert any("pubmed" in q.lower() for q in preset.seed_queries)
    assert "pubmed_search" in preset.tools_enabled


def test_load_stock_trading_preset_carries_safety_language():
    preset = load("stock_trading")
    extra = preset.synthesize_prompt_extra.lower()
    assert "never recommend" in extra
    assert "buy / sell / hold" in extra or "buy/sell/hold" in extra


def test_load_personal_docs_preset_is_corpus_only():
    preset = load("personal_docs")
    assert preset.searxng_categories == []
    assert preset.seed_queries == []
    assert "corpus_only" in preset.tools_enabled


def test_load_missing_preset_errors(tmp_path):
    with pytest.raises(FileNotFoundError):
        load("nonexistent", root=tmp_path)


# ── apply_preset ─────────────────────────────────────────────────────

def test_apply_preset_translates_corpus_path_to_env():
    preset = DomainPreset(name="x", corpus_path="/tmp/my-index")
    env = apply_preset(preset)
    assert env["LOCAL_CORPUS_PATH"] == "/tmp/my-index"


def test_apply_preset_translates_top_k_to_env():
    preset = DomainPreset(name="x", top_k_evidence=12)
    env = apply_preset(preset)
    assert env["TOP_K_EVIDENCE"] == "12"


def test_apply_preset_empty_when_no_overrides():
    preset = DomainPreset(name="x")
    env = apply_preset(preset)
    assert env == {}


# ── list_names ───────────────────────────────────────────────────────

def test_list_names_handles_missing_dir(tmp_path):
    nonexistent = tmp_path / "nope"
    assert list_names(root=nonexistent) == []


def test_list_names_is_sorted(tmp_path):
    for name in ["zeta", "alpha", "medical"]:
        (tmp_path / f"{name}.yaml").write_text(f"name: {name}\n")
    assert list_names(root=tmp_path) == ["alpha", "medical", "zeta"]


if __name__ == "__main__":
    sys.exit(pytest.main([__file__, "-v"]))
