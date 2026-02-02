#!/bin/bash

# IPPOC-OS Supervisor v1.0 (Hardened)
# "Layer 1: Boot & Process Orchestration"

# Colors
GREEN='\033[0;32m'
CYAN='\033[0;36m'
RED='\033[0;31m'
NC='\033[0m'
YELLOW='\033[0;33m'

LOG_DIR="logs"
mkdir -p $LOG_DIR

# --- SUPERVISOR FUNCTIONS ---

wait_for_port() {
  local port=$1
  local name=$2
  local timeout=30

  echo -n "Waiting for $name on port $port..."
  for i in $(seq 1 $timeout); do
    if curl -sI http://127.0.0.1:$port/health &>/dev/null || nc -z 127.0.0.1 $port 2>/dev/null; then
      echo -e "${GREEN} OK${NC}"
      return 0
    fi
    echo -n "."
    sleep 1
  done
  echo -e "${RED} FAILED${NC}"
  echo -e "${RED}CRITICAL: $name failed to bind port $port within $timeout seconds.${NC}"
  local log_name=$(echo "$name" | tr '[:upper:]' '[:lower:]')
  tail -n 20 "$LOG_DIR/${log_name}.log"
  exit 1
}

check_pid() {
  local pid=$1
  local name=$2
  if ! kill -0 $pid 2>/dev/null; then
    echo -e "${RED}CRITICAL: $name (PID $pid) died unexpectedly.${NC}"
    local log_name=$(echo "$name" | tr '[:upper:]' '[:lower:]')
    tail -n 20 "$LOG_DIR/${log_name}.log"
    exit 1
  fi
}

cleanup() {
  echo -e "\n${YELLOW}Supervisor: Initiating Graceful Shutdown...${NC}"
  [ -n "$MIND_PID" ] && kill $MIND_PID 2>/dev/null
  [ -n "$BODY_PID" ] && kill $BODY_PID 2>/dev/null
  [ -n "$CORTEX_PID" ] && kill $CORTEX_PID 2>/dev/null
  [ -n "$MEMORY_PID" ] && kill $MEMORY_PID 2>/dev/null
  # Force kill lingering ports
  lsof -ti:8000,8001,8089,19001,3000 | xargs kill -9 2>/dev/null
  exit
}

trap cleanup SIGINT SIGTERM

echo -e "${CYAN}IPPOC-OS Sovereign Swarm - Boot Sequence Initiated${NC}"

# --- BOOT SEQUENCE ---

# 0. Load Environment Variables
if [ -f .env ]; then
    echo -e "${YELLOW}[*] Loading .env...${NC}"
    set -a
    source .env
    set +a
elif [ -f mind/openclaw/.env.local ]; then
    echo -e "${YELLOW}[*] Loading mind/openclaw/.env.local...${NC}"
    set -a
    source mind/openclaw/.env.local
    set +a
else
    echo -e "${RED}[!] No .env file found. Services may fail if keys are missing.${NC}"
fi

# 0.1 Environment Check
# 0.1 Environment Checks
check_cmd() {
    if ! command -v "$1" &> /dev/null; then
        echo -e "${RED}[!] Missing requirement: $1${NC}"
        echo -e "${YELLOW}    Please install $1 to continue.${NC}"
        exit 1
    fi
}

echo -e "${YELLOW}[*] Validating Environment...${NC}"
check_cmd cargo
check_cmd python3
check_cmd node
check_cmd npm
check_cmd psql

# Check Postgres Connection & Extension
if ! psql -d ippoc -c "SELECT 1;" &> /dev/null; then
     echo -e "${RED}[!] Cannot connect to database 'ippoc'. Check credentials/running status.${NC}"
     # Don't exit, might be just starting up
else
     echo -e "${GREEN}    Database Connection: OK${NC}"
fi

# Global Python Path
export PYTHONPATH=$PYTHONPATH:$(pwd)

# 1. Start Memory (Limbic System)
echo -e "${GREEN}[1/4] Booting Memory (HiDB)...${NC}"
# Use generic python -m to pick up path
python3 -m uvicorn memory.api.server:app --host 0.0.0.0 --port 8000 > "$LOG_DIR/memory.log" 2>&1 &
MEMORY_PID=$!
wait_for_port 8000 "Memory"

# 2. Start Cortex (Reasoning Core)
echo -e "${GREEN}[2/4] Booting Cortex (Reasoning)...${NC}"
python3 brain/cortex/server.py > "$LOG_DIR/cortex.log" 2>&1 &
CORTEX_PID=$!
wait_for_port 8001 "Cortex"

# 3. Start Body (Sovereign Node)
echo -e "${GREEN}[3/4] Awakening Body (Rust Node)...${NC}"
# Requires build first to avoid race conditions in logs
cargo build --bin ippoc-node --quiet
cargo run --bin ippoc-node -- --port 8089 --role Reasoning > "$LOG_DIR/body.log" 2>&1 &
BODY_PID=$!
wait_for_port 8089 "Body"

# 4. Start Mind (Interface)
echo -e "${GREEN}[4/4] Opening Mind (OpenClaw)...${NC}"
cd mind/openclaw
sleep 5
OPENCLAW_GATEWAY_TOKEN=dev-token-insecure OPENCLAW_SKIP_CHANNELS=1 CLAWDBOT_SKIP_CHANNELS=1 node scripts/run-node.mjs --dev gateway --reset --token dev-token-insecure > "../../$LOG_DIR/mind.log" 2>&1 &
MIND_PID=$!
cd ../..
# Mind might take longer to compile Next.js, verify generic HTTP port or relax check
echo -e "${YELLOW}    Mind booting in background (GUI)...${NC}"

echo -e "${CYAN}---------------------------------------------------${NC}"
echo -e "${CYAN} SYSTEM ONLINE - SWARM SUPERVISOR ACTIVE${NC}"
echo -e "${CYAN}---------------------------------------------------${NC}"
echo -e "Memory:  http://localhost:8000/docs"
echo -e "Cortex:  http://localhost:8001/docs"
echo -e "Body:    http://localhost:8089/v1/economy/balance"
echo -e "Mind:    http://localhost:19001/?token=${OPENCLAW_GATEWAY_TOKEN:-dev-token-insecure} (Gateway)"
echo -e "Logs:    tail -f $LOG_DIR/*.log"

# --- SUPERVISOR LOOP ---
sleep 5
while true; do
  check_pid $MEMORY_PID "Memory" || MEMORY_PID=$(pgrep -f "uvicorn memory.api.server:app")
  check_pid $CORTEX_PID "Cortex" || CORTEX_PID=$(pgrep -f "brain/cortex/server.py")
  check_pid $BODY_PID "Body"   || BODY_PID=$(pgrep -f "ippoc-node")
  
  # Check Mind Gateway (19001)
  if ! curl -sf http://127.0.0.1:19001/health &>/dev/null && ! nc -z 127.0.0.1 19001 2>/dev/null; then
      echo -e "${RED}[warn] Mind Gateway (19001) is not responding.${NC}"
  fi
  sleep 10
done
