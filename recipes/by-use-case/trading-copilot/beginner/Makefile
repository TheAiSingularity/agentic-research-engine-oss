.PHONY: run smoke test install clean help

PY       ?= python3.12
VENV     ?= .venv
PYBIN    := $(VENV)/bin/python
PIPBIN   := $(VENV)/bin/pip
REPO_ROOT := $(abspath ../../../..)

help:
	@echo "Targets:"
	@echo "  install  — create .venv and install requirements"
	@echo "  run      — run the recipe against watchlist.example.yaml"
	@echo "  smoke    — same as run; verifies the live stack end-to-end"
	@echo "  test     — mocked unit tests (no network, no API keys)"
	@echo "  clean    — remove .venv"

$(PYBIN):
	$(PY) -m venv $(VENV)
	$(PIPBIN) install -q --upgrade pip
	$(PIPBIN) install -q -r requirements.txt

install: $(PYBIN)

run: $(PYBIN)
	PYTHONPATH=$(REPO_ROOT) $(PYBIN) main.py

smoke: $(PYBIN)
	PYTHONPATH=$(REPO_ROOT) $(PYBIN) main.py

test: $(PYBIN)
	PYTHONPATH=$(REPO_ROOT) $(PYBIN) -m pytest test_main.py -v

clean:
	rm -rf $(VENV) .pytest_cache __pycache__
