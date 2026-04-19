.PHONY: eval help

PY     ?= python3.12
VENV   := ../beginner/.venv
PYBIN  := $(VENV)/bin/python
REPO_ROOT := $(abspath ../../../..)

help:
	@echo "make eval    — run the agent over dataset.jsonl and print scores"
	@echo "Requires: EXA_API_KEY, GOOGLE_API_KEY, OPENAI_API_KEY."

eval:
	@test -n "$$EXA_API_KEY" || (echo "EXA_API_KEY not set" && exit 1)
	@test -n "$$GOOGLE_API_KEY" || (echo "GOOGLE_API_KEY not set" && exit 1)
	@test -n "$$OPENAI_API_KEY" || (echo "OPENAI_API_KEY not set" && exit 1)
	@test -x $(PYBIN) || $(MAKE) -C ../beginner install
	PYTHONPATH=$(REPO_ROOT) $(PYBIN) scorer.py dataset.jsonl
