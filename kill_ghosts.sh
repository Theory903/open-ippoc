#!/usr/bin/env bash
# ============================================================
# IPPOC Ghost Process Cleanup
# Kills orphaned Soma / Cortex / Gateway processes safely
# ============================================================

set -Eeuo pipefail

# ---------- UI ----------
RESET='\033[0m'
BOLD='\033[1m'
GREEN='\033[0;32m'
YELLOW='\033[0;33m'
RED='\033[0;31m'
BLUE='\033[0;34m'

info() { echo -e "${BLUE}ℹ $1${RESET}"; }
ok()   { echo -e "${GREEN}✔ $1${RESET}"; }
warn() { echo -e "${YELLOW}⚠ $1${RESET}"; }
fail() { echo -e "${RED}✖ $1${RESET}"; }

# ---------- Config ----------
PORTS=(8002 8003 19001)
PROCESS_PATTERNS=(
  "ippoc-node"
  "cortex.cortex.server"
  "openclaw"
  "gateway:dev"
)

# ---------- Helpers ----------
kill_pid() {
  local pid=$1 label=$2

  if kill -0 "$pid" 2>/dev/null; then
    info "Stopping $label (PID $pid)"
    kill "$pid" 2>/dev/null || true
    sleep 1
    if kill -0 "$pid" 2>/dev/null; then
      warn "$label did not exit, force killing"
      kill -9 "$pid" 2>/dev/null || true
    fi
    ok "$label terminated"
  fi
}

# ---------- Start ----------
echo -e "\n${BOLD}▶ IPPOC Ghost Cleanup${RESET}\n"

# 1. Kill by well-known ports (safest)
info "Cleaning processes bound to IPPOC ports"

for port in "${PORTS[@]}"; do
  pids=$(lsof -ti ":$port" 2>/dev/null || true)
  for pid in $pids; do
    cmd=$(ps -p "$pid" -o comm= || echo "unknown")
    kill_pid "$pid" "Port :$port ($cmd)"
  done
done

# 2. Kill orphaned binaries by signature
info "Cleaning orphaned IPPOC processes by signature"

for pattern in "${PROCESS_PATTERNS[@]}"; do
  pids=$(pgrep -f "$pattern" || true)
  for pid in $pids; do
    cmd=$(ps -p "$pid" -o command= || echo "unknown")
    kill_pid "$pid" "$pattern → $cmd"
  done
done

# 3. Final verification
sleep 1
remaining=0

for port in "${PORTS[@]}"; do
  if lsof -ti ":$port" >/dev/null 2>&1; then
    warn "Port $port still occupied"
    remaining=1
  fi
done

if [[ "$remaining" -eq 0 ]]; then
  ok "System is clean. No ghost processes detected."
else
  fail "Some ghost processes could not be terminated."
fi