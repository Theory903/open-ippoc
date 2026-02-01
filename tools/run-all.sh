#!/usr/bin/env bash
#
# IPPOC-OS Single Command Runner
# Runs node and cortex in parallel with proper logging
#

set -euo pipefail

# Colors
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Cleanup function
cleanup() {
    echo -e "\n${YELLOW}Shutting down IPPOC-OS...${NC}"
    kill $(jobs -p) 2>/dev/null || true
    wait
    echo -e "${GREEN}✓ Shutdown complete${NC}"
    exit 0
}

trap cleanup SIGINT SIGTERM

echo -e "${BLUE}"
cat << "EOF"
╔═══════════════════════════════════════════════════════════╗
║                  IPPOC-OS LAUNCHER                        ║
║   Running Node + Cortex in Parallel                      ║
╚═══════════════════════════════════════════════════════════╝
EOF
echo -e "${NC}"

# Check if .env exists
if [ ! -f .env ]; then
    echo -e "${RED}Error: .env file not found${NC}"
    echo -e "${YELLOW}Run ./tools/setup-databases.sh first${NC}"
    exit 1
fi

# Source environment
source .env

# Create log directory
mkdir -p logs

echo -e "${YELLOW}[1/3] Starting IPPOC Node...${NC}"

# Run node in background
cargo run --release --bin ippoc-node -- --port ${NODE_PORT:-9000} > logs/node.log 2>&1 &
NODE_PID=$!

sleep 3

if ! kill -0 $NODE_PID 2>/dev/null; then
    echo -e "${RED}✗ Node failed to start. Check logs/node.log${NC}"
    exit 1
fi

echo -e "${GREEN}✓ Node started (PID: $NODE_PID)${NC}"

echo -e "\n${YELLOW}[2/3] Starting OpenClaw Cortex...${NC}"

# Run cortex in background
cd apps/openclaw-cortex
pnpm start > ../../logs/cortex.log 2>&1 &
CORTEX_PID=$!
cd ../..

sleep 2

if ! kill -0 $CORTEX_PID 2>/dev/null; then
    echo -e "${RED}✗ Cortex failed to start. Check logs/cortex.log${NC}"
    kill $NODE_PID 2>/dev/null || true
    exit 1
fi

echo -e "${GREEN}✓ Cortex started (PID: $CORTEX_PID)${NC}"

echo -e "\n${YELLOW}[3/3] System Status${NC}"
echo -e "${GREEN}✓ IPPOC-OS is running!${NC}\n"

echo -e "${BLUE}Process IDs:${NC}"
echo -e "  Node:   ${GREEN}$NODE_PID${NC}"
echo -e "  Cortex: ${GREEN}$CORTEX_PID${NC}\n"

echo -e "${BLUE}Logs:${NC}"
echo -e "  Node:   ${GREEN}logs/node.log${NC}"
echo -e "  Cortex: ${GREEN}logs/cortex.log${NC}\n"

echo -e "${BLUE}View logs in real-time:${NC}"
echo -e "  ${YELLOW}tail -f logs/node.log${NC}"
echo -e "  ${YELLOW}tail -f logs/cortex.log${NC}\n"

echo -e "${BLUE}Databases:${NC}"
docker ps --filter "name=ippoc" --format "table {{.Names}}\t{{.Status}}\t{{.Ports}}"

echo -e "\n${YELLOW}Press Ctrl+C to stop all services${NC}\n"

# Monitor processes
while true; do
    if ! kill -0 $NODE_PID 2>/dev/null; then
        echo -e "${RED}✗ Node crashed! Check logs/node.log${NC}"
        kill $CORTEX_PID 2>/dev/null || true
        exit 1
    fi
    
    if ! kill -0 $CORTEX_PID 2>/dev/null; then
        echo -e "${RED}✗ Cortex crashed! Check logs/cortex.log${NC}"
        kill $NODE_PID 2>/dev/null || true
        exit 1
    fi
    
    sleep 5
done
