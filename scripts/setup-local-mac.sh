#!/usr/bin/env bash
# Set up the recipes' local dev stack on macOS.
#
#   * Ollama (LLM serving)  — OpenAI-compatible API at :11434/v1
#   * SearXNG (web search)  — JSON API at :8888
#   * gemma4:e2b pulled for research-assistant smoke tests
#
# Safe to re-run; every step is idempotent.
set -euo pipefail

here() { cd "$(dirname "$0")" && pwd; }
ROOT="$(cd "$(here)/.." && pwd)"

log() { printf '\033[1;34m▸\033[0m %s\n' "$*"; }
ok()  { printf '\033[1;32m✓\033[0m %s\n' "$*"; }
die() { printf '\033[1;31m✗\033[0m %s\n' "$*"; exit 1; }

command -v brew >/dev/null 2>&1 || die "Homebrew required — https://brew.sh"
command -v docker >/dev/null 2>&1 || die "Docker Desktop required — https://www.docker.com/products/docker-desktop"

# 1. Ollama
if ! command -v ollama >/dev/null 2>&1; then
  log "Installing Ollama via brew"
  brew install ollama
fi
if ! curl -sS http://localhost:11434/api/tags >/dev/null 2>&1; then
  log "Starting Ollama service"
  brew services start ollama
  for _ in $(seq 1 30); do
    sleep 1
    curl -sS http://localhost:11434/api/tags >/dev/null 2>&1 && break
  done
fi
ok "Ollama ready"

# 2. Pull the model (small — ~7GB, fine for Apple Silicon)
MODEL="${MODEL:-gemma4:e2b}"
if ! ollama list 2>/dev/null | awk 'NR>1 {print $1}' | grep -Fxq "$MODEL"; then
  log "Pulling $MODEL (one-time download, ~7GB)"
  ollama pull "$MODEL"
fi
ok "Model $MODEL available"

# 3. Docker daemon
if ! docker info >/dev/null 2>&1; then
  log "Starting Docker Desktop"
  open -a Docker
  for _ in $(seq 1 60); do
    sleep 2
    docker info >/dev/null 2>&1 && break
  done
fi
docker info >/dev/null 2>&1 || die "Docker daemon never became ready"
ok "Docker daemon up"

# 4. SearXNG via Docker Compose
cd "$ROOT/scripts/searxng"
if [ ! -f .env ]; then
  log "Generating SearXNG secret → .env"
  echo "SEARXNG_SECRET=$(openssl rand -hex 32)" > .env
fi
log "Bringing up SearXNG (docker compose up -d)"
docker compose up -d >/dev/null
for _ in $(seq 1 30); do
  sleep 1
  curl -sS "http://localhost:8888/search?q=test&format=json" >/dev/null 2>&1 && break
done
ok "SearXNG JSON API responding at http://localhost:8888"

cat <<EOF

$(printf '\033[1;32mLocal stack ready.\033[0m')

Next steps — run the research-assistant recipe with your local models:

  cd $ROOT/recipes/by-use-case/research-assistant/beginner
  make install

  export OPENAI_BASE_URL=http://localhost:11434/v1
  export OPENAI_API_KEY=ollama
  export MODEL_PLANNER=$MODEL
  export MODEL_SEARCHER=$MODEL
  export MODEL_SYNTHESIZER=$MODEL
  export SEARXNG_URL=http://localhost:8888

  make smoke

EOF
