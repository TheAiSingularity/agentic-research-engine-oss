#!/usr/bin/env bash
# Set up the local-inference stack on a Linux GPU VM.
#
#   * vLLM (LLM serving, CUDA) — OpenAI-compatible API at :8000/v1
#   * SearXNG (web search)     — JSON API at :8888
#
# Targets: Ubuntu 22.04/24.04 with a working CUDA + nvidia-smi. Written for a
# 4× RTX 6000 Pro Blackwell rig (384GB VRAM) but adjusts via env vars.
#
# Usage:  bash scripts/setup-vm-gpu.sh
#         bash scripts/setup-vm-gpu.sh --model Qwen/Qwen3.6-35B-A3B
#
set -euo pipefail

MODEL="${MODEL:-Qwen/Qwen3.6-35B-A3B}"      # primary frontier model
TENSOR_PARALLEL="${TENSOR_PARALLEL:-4}"     # one process per GPU
GPU_MEM_UTIL="${GPU_MEM_UTIL:-0.85}"
VLLM_PORT="${VLLM_PORT:-8000}"

# Parse --model
while [ $# -gt 0 ]; do
  case "$1" in
    --model) MODEL="$2"; shift 2;;
    --tp) TENSOR_PARALLEL="$2"; shift 2;;
    *) echo "unknown arg $1"; exit 1;;
  esac
done

here() { cd "$(dirname "$0")" && pwd; }
ROOT="$(cd "$(here)/.." && pwd)"

log() { printf '\033[1;34m▸\033[0m %s\n' "$*"; }
ok()  { printf '\033[1;32m✓\033[0m %s\n' "$*"; }
die() { printf '\033[1;31m✗\033[0m %s\n' "$*"; exit 1; }

command -v nvidia-smi >/dev/null 2>&1 || die "nvidia-smi not found — install NVIDIA drivers + CUDA first"
command -v docker >/dev/null 2>&1 || die "Docker required"

GPU_COUNT=$(nvidia-smi --query-gpu=name --format=csv,noheader | wc -l)
log "Detected $GPU_COUNT GPU(s):"
nvidia-smi --query-gpu=name,memory.total --format=csv
[ "$GPU_COUNT" -ge "$TENSOR_PARALLEL" ] || die "Need ≥$TENSOR_PARALLEL GPUs for tensor-parallel=$TENSOR_PARALLEL"

# 1. Python 3.12 + uv (fastest way to stand up vLLM)
if ! command -v uv >/dev/null 2>&1; then
  log "Installing uv (fast Python package manager)"
  curl -LsSf https://astral.sh/uv/install.sh | sh
  export PATH="$HOME/.local/bin:$PATH"
fi

# 2. vLLM in an isolated venv
VLLM_ROOT="$HOME/.cache/agentic-vllm"
mkdir -p "$VLLM_ROOT"
cd "$VLLM_ROOT"
if [ ! -d .venv ]; then
  log "Creating vLLM venv (Python 3.12)"
  uv venv --python 3.12
fi
if ! "$VLLM_ROOT/.venv/bin/python" -c "import vllm" >/dev/null 2>&1; then
  log "Installing vLLM (may take several minutes)"
  "$VLLM_ROOT/.venv/bin/pip" install --upgrade pip
  "$VLLM_ROOT/.venv/bin/pip" install "vllm>=0.6.0"
fi
ok "vLLM installed"

# 3. Start vLLM as a systemd user service (keeps running across SSH disconnects)
UNIT="$HOME/.config/systemd/user/agentic-vllm.service"
mkdir -p "$(dirname "$UNIT")"
cat > "$UNIT" <<EOF
[Unit]
Description=vLLM OpenAI-compatible server (agentic-ai-cookbook-lab)
After=network.target

[Service]
Type=simple
Environment=PATH=$HOME/.local/bin:/usr/local/bin:/usr/bin:/bin
ExecStart=$VLLM_ROOT/.venv/bin/python -m vllm.entrypoints.openai.api_server \\
  --model $MODEL \\
  --tensor-parallel-size $TENSOR_PARALLEL \\
  --gpu-memory-utilization $GPU_MEM_UTIL \\
  --port $VLLM_PORT \\
  --host 0.0.0.0
Restart=on-failure

[Install]
WantedBy=default.target
EOF

systemctl --user daemon-reload
systemctl --user enable --now agentic-vllm.service
log "Waiting for vLLM to warm up (loading $MODEL onto $TENSOR_PARALLEL GPUs)…"
for _ in $(seq 1 180); do
  sleep 5
  curl -sS "http://localhost:$VLLM_PORT/v1/models" >/dev/null 2>&1 && break
done
curl -sS "http://localhost:$VLLM_PORT/v1/models" >/dev/null || die "vLLM never became ready — check: journalctl --user -u agentic-vllm"
ok "vLLM serving $MODEL at http://localhost:$VLLM_PORT/v1"

# 4. SearXNG via Docker Compose
cd "$ROOT/scripts/searxng"
if [ ! -f .env ]; then
  echo "SEARXNG_SECRET=$(openssl rand -hex 32)" > .env
fi
docker compose up -d >/dev/null
for _ in $(seq 1 30); do
  sleep 1
  curl -sS "http://localhost:8888/search?q=test&format=json" >/dev/null 2>&1 && break
done
ok "SearXNG JSON API responding at http://localhost:8888"

cat <<EOF

$(printf '\033[1;32mVM stack ready.\033[0m')

Run the research-assistant recipe:

  cd $ROOT/recipes/by-use-case/research-assistant/beginner
  make install

  export OPENAI_BASE_URL=http://localhost:$VLLM_PORT/v1
  export OPENAI_API_KEY=vllm
  export MODEL_PLANNER=$MODEL
  export MODEL_SEARCHER=$MODEL
  export MODEL_SYNTHESIZER=$MODEL
  export SEARXNG_URL=http://localhost:8888

  make smoke

Manage vLLM:
  systemctl --user status  agentic-vllm
  systemctl --user restart agentic-vllm
  journalctl --user -u agentic-vllm -f

EOF
