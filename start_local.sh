#!/bin/bash
# start_local.sh - The IPPOC Local Development Launcher
# Starts all services on the host machine (No Docker)

set -e

# --- Colors ---
GREEN='\033[0;32m'
BLUE='\033[0;34m'
RED='\033[0;31m'
NC='\033[0m'

# --- Configuration ---
PYTHON_CMD="python3"
CARGO_CMD="cargo"
NODE_CMD="node"
PNPM_CMD="pnpm"

# --- Functions ---
cleanup() {
    echo -e "${RED}🛑 Shutting down all local services...${NC}"
    # Kill by port for robustness on macOS
    lsof -ti :8002,8003,19001 | xargs kill -9 2>/dev/null || true
    # Kill any foreground jobs
    jobs -p | xargs kill -9 2>/dev/null || true
}

# --- Trap for Cleanup ---
trap cleanup SIGINT SIGTERM

if [ "$1" == "stop" ]; then
    cleanup
    echo -e "${GREEN}✅ All services stopped.${NC}"
    exit 0
fi

# Pre-emptive cleanup to ensure ports are free
cleanup

echo -e "${GREEN}🌱 Initializing IPPOC Local Dev Environment...${NC}"

# 1. Environment Check
if [ ! -f ".env" ]; then
    echo -e "${RED}❌ .env file missing. Please create one from .env.example${NC}"
    exit 1
fi
export $(grep -v '^#' .env | xargs)

# 2. Mnemosyne (Memory) - Redis/Postgres assumed running
echo -e "${BLUE}🧠 Waking Mnemosyne (Memory)...${NC}"
# For local dev, we assume Redis and Postgres are running via brew or system services
# Mnemosyne logic is currently embedded or via direct python execution if standalone
# Creating a placeholder or starting if it exists as a separate python module
if [ -d "src/mnemosyne" ]; then
    # Assuming it's a python module
    echo "   (Mnemosyne is integrated, ensuring dependencies...)"
fi

# 3. Soma (Body) - Rust
echo -e "${BLUE}💪 Flexing Soma (Body)...${NC}"
cd src/soma
$CARGO_CMD run --bin ippoc-node -- --port 8002 &
SOMA_PID=$!
cd ../..
echo "   Soma PID: $SOMA_PID"

# Wait for Soma to be ready (naive sleep)
sleep 2

# 4. Cortex (Brain) - Python
echo -e "${BLUE}⚡ Igniting Cortex (Brain)...${NC}"
# Ensure requirements are met
# pip install -r src/cortex/requirements.txt > /dev/null
export PYTHONPATH=$PYTHONPATH:$(pwd)/src
$PYTHON_CMD -m cortex.cortex.server --port 8003 &
CORTEX_PID=$!
echo "   Cortex PID: $CORTEX_PID"

# 5. OpenClaw Gateway (Kernel) - Node.js
echo -e "${BLUE}🚪 Opening Gateway...${NC}"
cd src/kernel/openclaw
if [ ! -d "node_modules" ]; then
    echo -e "${YELLOW}📦 Installing OpenClaw dependencies...${NC}"
    $PNPM_CMD install
fi
# Build if needed, or run dev
$PNPM_CMD run gateway:dev &
GATEWAY_PID=$!
cd ../../..
echo "   Gateway PID: $GATEWAY_PID"

echo -e "${GREEN}🚀 IPPOC Local System is ALIVE!${NC}"
echo "   - Soma (Rust): http://localhost:8002"
echo "   - Cortex (Python): http://localhost:8003"
echo "   - Gateway (Node): http://localhost:19001"
echo ""
echo -e "${BLUE}Press Ctrl+C to stop all services.${NC}"

# Keep script running to maintain trap
wait
