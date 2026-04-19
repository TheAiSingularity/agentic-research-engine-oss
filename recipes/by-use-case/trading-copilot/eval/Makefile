.PHONY: eval help clean

PY     ?= python3.12
VENV   := ../beginner/.venv
PYBIN  := $(VENV)/bin/python
REPO_ROOT := $(abspath ../../../..)

help:
	@echo "make eval   — run backtest over fixtures/sample_window.yaml"
	@echo ""
	@echo "Requires the beginner tier installed (../beginner/.venv)."
	@echo "Uses whatever LLM backend is configured via OPENAI_BASE_URL."

eval:
	PYTHONPATH=$(REPO_ROOT) $(PYBIN) backtest.py fixtures/sample_window.yaml

clean:
	rm -rf __pycache__ .pytest_cache
