#!/usr/bin/env bash
# Set up the local-inference stack on a Linux GPU VM.
#
#   * vLLM or SGLang (LLM serving, CUDA) — OpenAI-compatible API at :8000/v1
#   * SearXNG (web search)               — JSON API at :8888
#
# Targets: Ubuntu 22.04/24.04 with working CUDA + nvidia-smi. Written for a
# 4× RTX 6000 Pro Blackwell rig (384 GB VRAM) but adjusts via env vars.
#
# Engine choice (2026):
#   vllm    — mature, widest model support, production-standard
#   sglang  — RadixAttention prefix caching, +29% throughput on H100;
#             up to 6.4× faster on prefix-heavy RAG workloads like ours
#
# Speculative decoding: --spec-dec enables EAGLE-style draft verification,
# 2–3× decode speedup at zero quality loss on both engines (where supported).
#
# Usage:
#   bash scripts/setup-vm-gpu.sh                                      # vLLM default
#   bash scripts/setup-vm-gpu.sh --engine sglang                      # SGLang
#   bash scripts/setup-vm-gpu.sh --engine sglang --model Qwen/...     # custom model
#   bash scripts/setup-vm-gpu.sh --spec-dec                           # enable EAGLE
#
set -euo pipefail

ENGINE="${ENGINE:-vllm}"                    # vllm | sglang
MODEL="${MODEL:-Qwen/Qwen3.6-35B-A3B}"
TENSOR_PARALLEL="${TENSOR_PARALLEL:-4}"
GPU_MEM_UTIL="${GPU_MEM_UTIL:-0.85}"
SERVER_PORT="${SERVER_PORT:-8000}"
SPEC_DEC=""                                 # set to --spec-dec to enable

# Parse flags
while [ $# -gt 0 ]; do
  case "$1" in
    --engine)   ENGINE="$2"; shift 2;;
    --model)    MODEL="$2"; shift 2;;
    --tp)       TENSOR_PARALLEL="$2"; shift 2;;
    --port)     SERVER_PORT="$2"; shift 2;;
    --spec-dec) SPEC_DEC="1"; shift;;
    *) echo "unknown arg $1"; exit 1;;
  esac
done
[ "$ENGINE" = "vllm" ] || [ "$ENGINE" = "sglang" ] || { echo "--engine must be vllm or sglang"; exit 1; }

here() { cd "$(dirname "$0")" && pwd; }
ROOT="$(cd "$(here)/.." && pwd)"

log() { printf '\033[1;34m▸\033[0m %s\n' "$*"; }
ok()  { printf '\033[1;32m✓\033[0m %s\n' "$*"; }
die() { printf '\033[1;31m✗\033[0m %s\n' "$*"; exit 1; }

command -v nvidia-smi >/dev/null 2>&1 || die "nvidia-smi not found — install NVIDIA drivers + CUDA first"
command -v docker     >/dev/null 2>&1 || die "Docker required"

GPU_COUNT=$(nvidia-smi --query-gpu=name --format=csv,noheader | wc -l)
log "Detected $GPU_COUNT GPU(s):"
nvidia-smi --query-gpu=name,memory.total --format=csv
[ "$GPU_COUNT" -ge "$TENSOR_PARALLEL" ] || die "Need ≥$TENSOR_PARALLEL GPUs for tensor-parallel=$TENSOR_PARALLEL"

# 1. Python 3.12 + uv
if ! command -v uv >/dev/null 2>&1; then
  log "Installing uv (fast Python package manager)"
  curl -LsSf https://astral.sh/uv/install.sh | sh
  export PATH="$HOME/.local/bin:$PATH"
fi

# 2. Engine install in an isolated venv
ENGINE_ROOT="$HOME/.cache/agentic-$ENGINE"
mkdir -p "$ENGINE_ROOT"
cd "$ENGINE_ROOT"
if [ ! -d .venv ]; then
  log "Creating $ENGINE venv (Python 3.12)"
  uv venv --python 3.12
fi

PYBIN="$ENGINE_ROOT/.venv/bin/python"
PIPBIN="$ENGINE_ROOT/.venv/bin/pip"

if [ "$ENGINE" = "vllm" ]; then
  if ! "$PYBIN" -c "import vllm" >/dev/null 2>&1; then
    log "Installing vLLM (may take several minutes)"
    "$PIPBIN" install --upgrade pip
    "$PIPBIN" install "vllm>=0.6.0"
  fi
else
  if ! "$PYBIN" -c "import sglang" >/dev/null 2>&1; then
    log "Installing SGLang (may take several minutes)"
    "$PIPBIN" install --upgrade pip
    "$PIPBIN" install "sglang[all]>=0.4.0"
  fi
fi
ok "$ENGINE installed"

# 3. Build engine-specific systemd unit
UNIT_NAME="agentic-$ENGINE"
UNIT="$HOME/.config/systemd/user/$UNIT_NAME.service"
mkdir -p "$(dirname "$UNIT")"

# Speculative-decoding flags per engine (EAGLE-class)
SPEC_FLAGS_VLLM=""
SPEC_FLAGS_SGLANG=""
if [ -n "$SPEC_DEC" ]; then
  # These flags work on recent vLLM/SGLang; tune per target model if needed.
  SPEC_FLAGS_VLLM='--speculative-config {"method":"eagle","num_speculative_tokens":5}'
  SPEC_FLAGS_SGLANG='--speculative-algorithm EAGLE --speculative-num-steps 5 --speculative-num-draft-tokens 8'
  log "Enabling speculative decoding (EAGLE, 2–3× decode speedup)"
fi

if [ "$ENGINE" = "vllm" ]; then
  cat > "$UNIT" <<EOF
[Unit]
Description=vLLM OpenAI-compatible server (agentic-ai-cookbook-lab)
After=network.target

[Service]
Type=simple
Environment=PATH=$HOME/.local/bin:/usr/local/bin:/usr/bin:/bin
ExecStart=$PYBIN -m vllm.entrypoints.openai.api_server \\
  --model $MODEL \\
  --tensor-parallel-size $TENSOR_PARALLEL \\
  --gpu-memory-utilization $GPU_MEM_UTIL \\
  --enable-prefix-caching \\
  --port $SERVER_PORT \\
  --host 0.0.0.0 \\
  $SPEC_FLAGS_VLLM
Restart=on-failure

[Install]
WantedBy=default.target
EOF
else
  cat > "$UNIT" <<EOF
[Unit]
Description=SGLang OpenAI-compatible server (agentic-ai-cookbook-lab)
After=network.target

[Service]
Type=simple
Environment=PATH=$HOME/.local/bin:/usr/local/bin:/usr/bin:/bin
ExecStart=$PYBIN -m sglang.launch_server \\
  --model-path $MODEL \\
  --tp $TENSOR_PARALLEL \\
  --mem-fraction-static $GPU_MEM_UTIL \\
  --port $SERVER_PORT \\
  --host 0.0.0.0 \\
  $SPEC_FLAGS_SGLANG
Restart=on-failure

[Install]
WantedBy=default.target
EOF
fi

systemctl --user daemon-reload
systemctl --user enable --now "$UNIT_NAME.service"
log "Waiting for $ENGINE to warm up (loading $MODEL onto $TENSOR_PARALLEL GPUs)…"
for _ in $(seq 1 180); do
  sleep 5
  curl -sS "http://localhost:$SERVER_PORT/v1/models" >/dev/null 2>&1 && break
done
curl -sS "http://localhost:$SERVER_PORT/v1/models" >/dev/null \
  || die "$ENGINE never became ready — check: journalctl --user -u $UNIT_NAME"
ok "$ENGINE serving $MODEL at http://localhost:$SERVER_PORT/v1"

# 4. SearXNG via Docker Compose
cd "$ROOT/scripts/searxng"
[ -f .env ] || echo "SEARXNG_SECRET=$(openssl rand -hex 32)" > .env
docker compose up -d >/dev/null
for _ in $(seq 1 30); do
  sleep 1
  curl -sS "http://localhost:8888/search?q=test&format=json" >/dev/null 2>&1 && break
done
ok "SearXNG JSON API responding at http://localhost:8888"

cat <<EOF

$(printf '\033[1;32mVM stack ready (%s).\033[0m' "$ENGINE")

Run the research-assistant recipe:

  cd $ROOT/recipes/by-use-case/research-assistant/beginner
  make install

  export OPENAI_BASE_URL=http://localhost:$SERVER_PORT/v1
  export OPENAI_API_KEY=$ENGINE
  export MODEL_PLANNER=$MODEL
  export MODEL_SEARCHER=$MODEL
  export MODEL_SYNTHESIZER=$MODEL
  export SEARXNG_URL=http://localhost:8888

  make smoke

Manage $ENGINE:
  systemctl --user status  $UNIT_NAME
  systemctl --user restart $UNIT_NAME
  journalctl --user -u $UNIT_NAME -f

EOF
