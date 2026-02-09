#!/usr/bin/env bash
# ============================================================
# IPPOC Local Orchestrator — Professional Edition
# ============================================================

set -Eeuo pipefail

# ---------- UI ----------
RESET='\033[0m'
BOLD='\033[1m'
DIM='\033[2m'
GREEN='\033[0;32m'
BLUE='\033[0;34m'
YELLOW='\033[0;33m'
RED='\033[0;31m'
CYAN='\033[0;36m'

ok()    { echo -e "${GREEN}✔ $1${RESET}"; }
info()  { echo -e "${BLUE}ℹ $1${RESET}"; }
warn()  { echo -e "${YELLOW}⚠ $1${RESET}"; }
fail()  { echo -e "${RED}✖ $1${RESET}"; exit 1; }
phase() { echo -e "\n${BOLD}${CYAN}▶ $1${RESET}"; }

# ---------- Config ----------
ROOT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PYTHON_CMD="${PYTHON_CMD:-python3}"
CARGO_CMD="${CARGO_CMD:-cargo}"
PNPM_CMD="${PNPM_CMD:-pnpm}"

PORT_SOMA=8002
PORT_CORTEX=8003
PORT_GATEWAY=19001

PIDS=()

# ---------- Utils ----------
require() {
  command -v "$1" >/dev/null || fail "Missing dependency: $1"
}

wait_for_port() {
  local port=$1 name=$2 timeout=20
  for ((i=0;i<timeout;i++)); do
    lsof -i ":$port" >/dev/null && ok "$name ready on :$port" && return 0
    sleep 1
  done
  fail "$name failed to start on port $port"
}

graceful_kill() {
  local pid=$1 name=$2
  if kill -0 "$pid" 2>/dev/null; then
    info "Stopping $name (PID $pid)"
    kill "$pid" 2>/dev/null || true
    sleep 2
    kill -9 "$pid" 2>/dev/null || true
  fi
}

cleanup() {
  echo
  phase "Shutdown"
  for entry in "${PIDS[@]}"; do
    IFS=":" read -r pid name <<< "$entry"
    graceful_kill "$pid" "$name"
  done
  ok "All services stopped"
}

trap cleanup INT TERM

# ---------- Stop Mode ----------
if [[ "${1:-}" == "stop" ]]; then
  cleanup
  exit 0
fi

# ---------- Phase 0: Preconditions ----------
phase "Preflight Checks"

require "$PYTHON_CMD"
require "$CARGO_CMD"
require "$PNPM_CMD"
require lsof

[[ -f "$ROOT_DIR/.env" ]] || fail ".env missing (copy from .env.example)"
export $(grep -v '^#' "$ROOT_DIR/.env" | xargs)

ok "Environment OK"

# ---------- Phase 1: Memory ----------
phase "Mnemosyne (Memory)"

info "Assuming Redis/Postgres managed externally"
ok "Memory layer assumed available"

# ---------- Phase 2: Soma ----------
phase "Soma (Rust Body)"

cd "$ROOT_DIR/src/soma"
"$CARGO_CMD" build --quiet
"$CARGO_CMD" run --bin ippoc-node -- --port "$PORT_SOMA" &
SOMA_PID=$!
PIDS+=("$SOMA_PID:Soma")
wait_for_port "$PORT_SOMA" "Soma"
cd "$ROOT_DIR"

# ---------- Phase 3: Cortex ----------
phase "Cortex (Python Brain)"

export PYTHONPATH="$ROOT_DIR/src"
"$PYTHON_CMD" -m cortex.cortex.server --port "$PORT_CORTEX" &
CORTEX_PID=$!
PIDS+=("$CORTEX_PID:Cortex")
wait_for_port "$PORT_CORTEX" "Cortex"

# ---------- Phase 4: Gateway ----------
phase "OpenClaw Gateway"

cd "$ROOT_DIR/src/kernel/openclaw"
[[ -d node_modules ]] || { info "Installing dependencies"; "$PNPM_CMD" install; }
"$PNPM_CMD" run gateway:dev &
GATEWAY_PID=$!
PIDS+=("$GATEWAY_PID:Gateway")
wait_for_port "$PORT_GATEWAY" "Gateway"
cd "$ROOT_DIR"

# ---------- Phase 5: Verification ----------
phase "System Verification"

curl -sf "http://localhost:$PORT_SOMA/health"   >/dev/null && ok "Soma healthy"   || warn "Soma health endpoint missing"
curl -sf "http://localhost:$PORT_CORTEX/health" >/dev/null && ok "Cortex healthy" || warn "Cortex health endpoint missing"

# ---------- Phase 6: Live ----------
phase "IPPOC is LIVE"

cat <<EOF

${BOLD}Services:${RESET}
  Soma    → http://localhost:$PORT_SOMA
  Cortex  → http://localhost:$PORT_CORTEX
  Gateway → http://localhost:$PORT_GATEWAY

${DIM}Press Ctrl+C to shut down cleanly.${RESET}
EOF

wait