.PHONY: run smoke test install clean help

PY       ?= python3.12
VENV     ?= .venv
PYBIN    := $(VENV)/bin/python
PIPBIN   := $(VENV)/bin/pip
REPO_ROOT := $(abspath ../../../..)

help:
	@echo "Targets:"
	@echo "  install  — create .venv and install requirements"
	@echo "  run      — ask a question against DOCS_DIR (or CORPUS_PATH)"
	@echo "  smoke    — ask a canned question against the fixture corpus"
	@echo "  test     — mocked unit tests (no API key, no network)"
	@echo "  clean    — remove .venv"

$(PYBIN):
	$(PY) -m venv $(VENV)
	$(PIPBIN) install -q --upgrade pip
	$(PIPBIN) install -q -r requirements.txt

install: $(PYBIN)

run: $(PYBIN)
	PYTHONPATH=$(REPO_ROOT) $(PYBIN) main.py "$(Q)"

smoke: $(PYBIN)
	DOCS_DIR=fixtures/sample_corpus \
	PYTHONPATH=$(REPO_ROOT) $(PYBIN) main.py \
	  "What retrieval techniques does the cookbook ship, and what does each do?"

test: $(PYBIN)
	PYTHONPATH=$(REPO_ROOT) $(PYBIN) -m pytest test_main.py -v

clean:
	rm -rf $(VENV) .pytest_cache __pycache__
