#!/usr/bin/env bash
# ============================================================
# IPPOC Local Orchestrator — Professional Math-Driven TUI
# ============================================================

set -Eeuo pipefail

# -------------------- Colors & Style --------------------
RESET='\033[0m'
BOLD='\033[1m'
DIM='\033[2m'
GREEN='\033[0;32m'
BLUE='\033[0;34m'
YELLOW='\033[0;33m'
RED='\033[0;31m'
CYAN='\033[0;36m'

ok()    { echo -e "${GREEN}✔${RESET} $1"; }
info()  { echo -e "${BLUE}ℹ${RESET} $1"; }
warn()  { echo -e "${YELLOW}⚠${RESET} $1"; }
fail()  { echo -e "${RED}✖${RESET} $1"; exit 1; }

# -------------------- TUI Math --------------------
term_width() {
  tput cols 2>/dev/null || echo 80
}

repeat_char() {
  local char="$1" count="$2"
  printf "%*s" "$count" "" | tr ' ' "$char"
}

clamp() {
  local val="$1" min="$2" max="$3"
  (( val < min )) && echo "$min" && return
  (( val > max )) && echo "$max" && return
  echo "$val"
}

box() {
  local title="$1"
  local padding=2
  local min_width=40

  local term_w
  term_w=$(term_width)

  local title_len=${#title}
  local content_w=$(( title_len + padding * 2 ))

  local width
  width=$(clamp "$content_w" "$min_width" "$((term_w - 4))")

  local inner_w=$(( width - 2 ))
  local left_pad=$(( (inner_w - title_len) / 2 ))
  local right_pad=$(( inner_w - title_len - left_pad ))

  echo
  echo "┌$(repeat_char "─" "$inner_w")┐"
  echo "│$(repeat_char " " "$left_pad")$title$(repeat_char " " "$right_pad")│"
  echo "└$(repeat_char "─" "$inner_w")┘"
}

section() {
  local title="$1"
  local prefix="▶ "
  local term_w
  term_w=$(term_width)

  local used=$(( ${#prefix} + ${#title} + 1 ))
  local line_w
  line_w=$(clamp "$((term_w - used))" 4 60)

  echo
  echo -e "${BOLD}${prefix}${title} $(repeat_char "─" "$line_w")${RESET}"
}

item_ok()   { echo -e "  ${GREEN}✔${RESET} $1"; }
item_warn() { echo -e "  ${YELLOW}⚠${RESET} $1"; }
item_fail() { echo -e "  ${RED}✖${RESET} $1"; }

# -------------------- Config --------------------
ROOT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PYTHON_CMD="${PYTHON_CMD:-python3}"
CARGO_CMD="${CARGO_CMD:-cargo}"
PNPM_CMD="${PNPM_CMD:-pnpm}"

PORT_SOMA=8002
PORT_CORTEX=8003
PORT_GATEWAY=19001

PIDS=()
DEGRADED=0

# -------------------- Utils --------------------
require() { command -v "$1" >/dev/null || fail "Missing dependency: $1"; }

wait_for_port() {
  local port=$1 name=$2 timeout=${3:-25}
  for ((i=0;i<timeout;i++)); do
    lsof -i ":$port" >/dev/null 2>&1 && item_ok "$name bound to :$port" && return 0
    sleep 1
  done
  item_fail "$name failed to bind :$port"
  return 1
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
  box "Shutdown"
  for entry in "${PIDS[@]}"; do
    IFS=":" read -r pid name <<< "$entry"
    graceful_kill "$pid" "$name"
  done
  ok "All services stopped"
}

trap cleanup INT TERM

# -------------------- Stop Mode --------------------
if [[ "${1:-}" == "stop" ]]; then
  cleanup
  exit 0
fi

# -------------------- Ghost Cleanup --------------------
if [[ -x "$ROOT_DIR/kill_ghosts.sh" ]]; then
  info "Cleaning ghost processes"
  "$ROOT_DIR/kill_ghosts.sh" || warn "Ghost cleanup reported issues"
fi

# -------------------- Header --------------------
box "IPPOC LOCAL ORCHESTRATOR"
echo -e "Node: ${BOLD}Local${RESET}  •  Profile: ${BOLD}Dev${RESET}  •  Mode: ${BOLD}Host${RESET}"

# -------------------- Phase 0: Preflight --------------------
section "Preflight Checks"
require "$PYTHON_CMD"
require "$CARGO_CMD"
require "$PNPM_CMD"
require lsof

[[ -f "$ROOT_DIR/.env" ]] || fail ".env missing (copy from .env.example)"
export $(grep -v '^#' "$ROOT_DIR/.env" | xargs)
item_ok "Environment OK"

# -------------------- Phase 1: Mnemosyne --------------------
section "Mnemosyne (Memory)"
item_ok "Redis/Postgres assumed externally managed"

# -------------------- Phase 2: Soma --------------------
section "Soma (Rust Body)"
cd "$ROOT_DIR/src/ippoc/soma"
"$CARGO_CMD" build --quiet
"$CARGO_CMD" run --bin ippoc-node -- --port "$PORT_SOMA" \
  2>&1 | sed 's/^/  │ SOMA │ /' &
SOMA_PID=$!
PIDS+=("$SOMA_PID:Soma")
cd "$ROOT_DIR"

wait_for_port "$PORT_SOMA" "Soma" || DEGRADED=1

# -------------------- Phase 3: Cortex --------------------
section "Cortex (Python Brain)"
export PYTHONPATH="$ROOT_DIR/src"
"$PYTHON_CMD" -m ippoc.cortex.cortex.server --port "$PORT_CORTEX" 2>&1 | awk '!seen[$0]++' | sed 's/^/  │ CORTEX │ /' &
CORTEX_PID=$!
PIDS+=("$CORTEX_PID:Cortex")

wait_for_port "$PORT_CORTEX" "Cortex" || DEGRADED=1

# -------------------- Phase 4: Gateway --------------------
section "OpenClaw Gateway"
cd "$ROOT_DIR/src/kernel/openclaw"
[[ -d node_modules ]] || { info "Installing dependencies"; "$PNPM_CMD" install; }
# Set gateway token to match IPPOC's expected token
export OPENCLAW_GATEWAY_TOKEN="ippoc-dev-token"
"$PNPM_CMD" run gateway:dev \
  2>&1 | awk '!seen[$0]++' | sed 's/^/  │ GATEWAY │ /' &
GATEWAY_PID=$!
PIDS+=("$GATEWAY_PID:Gateway")
cd "$ROOT_DIR"

wait_for_port "$PORT_GATEWAY" "Gateway" || DEGRADED=1

# -------------------- Phase 5: Verification --------------------
section "Verification"
if curl -sf "http://localhost:$PORT_SOMA/health" >/dev/null; then
  item_ok "Soma health OK"
else
  item_warn "Soma health endpoint unavailable"
  DEGRADED=1
fi

if curl -sf "http://localhost:$PORT_CORTEX/health" >/dev/null; then
  item_ok "Cortex health OK"
else
  item_warn "Cortex health endpoint unavailable"
  DEGRADED=1
fi

# -------------------- System State --------------------
box "SYSTEM STATE"
if [[ "$DEGRADED" -eq 0 ]]; then
  echo -e "  ${GREEN}🟢 HEALTHY${RESET}"
else
  echo -e "  ${YELLOW}🟡 DEGRADED${RESET}"
  echo -e "     • One or more subsystems reported warnings"
  echo -e "     • Filesystem skills active if TSBridge degraded"
fi

# -------------------- Footer --------------------
cat <<EOF

${BOLD}Endpoints:${RESET}
  Soma    → http://localhost:${PORT_SOMA}
  Cortex  → http://localhost:${PORT_CORTEX}
  Gateway → http://localhost:${PORT_GATEWAY}

${DIM}Press Ctrl+C to shut down cleanly.${RESET}
EOF

wait