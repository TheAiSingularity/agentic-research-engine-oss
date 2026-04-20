.PHONY: install test cli tui gui mcp smoke bench clean help

PY       ?= python3.12
VENV     ?= .venv
PYBIN    := $(VENV)/bin/python
PIPBIN   := $(VENV)/bin/pip
REPO_ROOT := $(abspath ..)

help:
	@echo "engine/ \u2014 targets:"
	@echo "  install  create .venv + install engine requirements"
	@echo "  test     mocked unit tests (no API key, no network)"
	@echo "  cli      run the CLI on the canonical question (Phase 3)"
	@echo "  tui      launch the Textual TUI (Phase 3)"
	@echo "  gui      launch the FastAPI + HTMX GUI on :8080 (Phase 3)"
	@echo "  mcp      start the Python MCP server on stdio (Phase 4)"
	@echo "  smoke    end-to-end against Ollama gemma3:4b + SearXNG"
	@echo "  bench    run the mini benchmark suite (Phase 8)"
	@echo "  clean    rm -rf .venv + caches"

$(PYBIN):
	$(PY) -m venv $(VENV)
	$(PIPBIN) install -q --upgrade pip
	$(PIPBIN) install -q -r requirements.txt

install: $(PYBIN)

test: $(PYBIN)
	PYTHONPATH=$(REPO_ROOT) $(PYBIN) -m pytest tests/ -v

cli: $(PYBIN)
	PYTHONPATH=$(REPO_ROOT) $(PYBIN) -m engine.interfaces.cli "$(Q)"

tui: $(PYBIN)
	PYTHONPATH=$(REPO_ROOT) $(PYBIN) -m engine.interfaces.tui

gui: $(PYBIN)
	PYTHONPATH=$(REPO_ROOT) $(PYBIN) -m uvicorn engine.interfaces.web.app:app --host 127.0.0.1 --port 8080 --reload

mcp: $(PYBIN)
	PYTHONPATH=$(REPO_ROOT) $(PYBIN) -m engine.mcp.server

smoke: $(PYBIN)
	OPENAI_BASE_URL=http://localhost:11434/v1 OPENAI_API_KEY=ollama \
	MODEL_PLANNER=gemma3:4b MODEL_SEARCHER=gemma3:4b MODEL_SYNTHESIZER=gemma3:4b \
	MODEL_VERIFIER=gemma3:4b MODEL_CRITIC=gemma3:4b MODEL_ROUTER=gemma3:4b MODEL_COMPRESSOR=gemma3:4b \
	EMBED_MODEL=nomic-embed-text SEARXNG_URL=http://localhost:8888 \
	PYTHONPATH=$(REPO_ROOT) $(PYBIN) -m engine.core.pipeline \
	  "What is Anthropic's contextual retrieval and why does it reduce retrieval failures?"

bench: $(PYBIN)
	PYTHONPATH=$(REPO_ROOT) $(PYBIN) benchmarks/runner.py

clean:
	rm -rf $(VENV) .pytest_cache __pycache__ **/__pycache__
