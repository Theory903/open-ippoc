#!/usr/bin/env bash
#
# IPPOC-OS Quick Start Script (No Docker Version)
# For running without Docker Desktop
#

set -euo pipefail

# Colors
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

echo -e "${BLUE}"
cat << "EOF"
╔═══════════════════════════════════════════════════════════╗
║                                                           ║
║   ██╗██████╗ ██████╗  ██████╗  ██████╗      ██████╗ ███████╗
║   ██║██╔══██╗██╔══██╗██╔═══██╗██╔════╝     ██╔═══██╗██╔════╝
║   ██║██████╔╝██████╔╝██║   ██║██║          ██║   ██║███████╗
║   ██║██╔═══╝ ██╔═══╝ ██║   ██║██║          ██║   ██║╚════██║
║   ██║██║     ██║     ╚██████╔╝╚██████╗     ╚██████╔╝███████║
║   ╚═╝╚═╝     ╚═╝      ╚═════╝  ╚═════╝      ╚═════╝ ╚══════╝
║                                                           ║
║   Intelligent, Participatory, Persistent, Organic Computing
║   (No Docker Version - Using Mock Databases)              ║
║                                                           ║
╚═══════════════════════════════════════════════════════════╝
EOF
echo -e "${NC}"

echo -e "${GREEN}Quick Start Script (No Docker)${NC}\n"

# Check prerequisites
echo -e "${YELLOW}[1/4] Checking prerequisites...${NC}"

if ! command -v cargo &> /dev/null; then
    echo -e "${RED}✗ Rust not found. Install from https://rustup.rs${NC}"
    exit 1
fi
echo -e "${GREEN}✓ Rust installed${NC}"

if ! command -v pnpm &> /dev/null; then
    echo -e "${YELLOW}⚠ pnpm not found. Installing...${NC}"
    npm install -g pnpm
fi
echo -e "${GREEN}✓ pnpm installed${NC}"

# Build Rust workspace
echo -e "\n${YELLOW}[2/4] Building Rust workspace...${NC}"
cargo build --workspace --release

echo -e "${GREEN}✓ Rust build complete${NC}"

# Build TypeScript apps
echo -e "\n${YELLOW}[3/4] Building TypeScript apps...${NC}"
cd apps/openclaw-cortex
pnpm install
pnpm build
cd ../..

echo -e "${GREEN}✓ TypeScript build complete${NC}"

# Create environment file (mock databases)
echo -e "\n${YELLOW}[4/4] Creating environment file (mock mode)...${NC}"

cat > .env << EOF
# Mock database connections (no actual databases)
DATABASE_URL=postgresql://mock:mock@localhost:5432/mock
REDIS_URL=redis://localhost:6379

# Node configuration
NODE_PORT=9000
NODE_ROLE=reasoning

# LLM configuration (optional)
VLLM_ENDPOINT=http://localhost:8000/v1

# Feature flags
ENABLE_SELF_EVOLUTION=false
ENABLE_TOOLSMITH=false

# Mock mode
MOCK_DATABASES=true
EOF

echo -e "${GREEN}✓ Environment file created (mock mode)${NC}"

# Success
echo -e "\n${GREEN}╔═══════════════════════════════════════════════════════════╗${NC}"
echo -e "${GREEN}║                                                           ║${NC}"
echo -e "${GREEN}║   ✓ IPPOC-OS Build Complete!                              ║${NC}"
echo -e "${GREEN}║                                                           ║${NC}"
echo -e "${GREEN}╚═══════════════════════════════════════════════════════════╝${NC}\n"

echo -e "${YELLOW}⚠ Running in MOCK MODE (no databases)${NC}"
echo -e "${YELLOW}For full functionality, start Docker Desktop and run:${NC}"
echo -e "${GREEN}  ./tools/quickstart.sh${NC}\n"

echo -e "${BLUE}Next steps (Mock Mode):${NC}\n"

echo -e "${YELLOW}1. Run IPPOC Node (Terminal 1):${NC}"
echo -e "   ${GREEN}source .env && cargo run --release --bin ippoc-node -- --port 9000${NC}\n"

echo -e "${YELLOW}2. Run OpenClaw Cortex (Terminal 2):${NC}"
echo -e "   ${GREEN}cd apps/openclaw-cortex && source ../../.env && pnpm start${NC}\n"

echo -e "${BLUE}Note:${NC} Mock mode runs without databases. Some features disabled:\n"
echo -e "   ${RED}✗${NC} HiDB memory storage"
echo -e "   ${RED}✗${NC} Redis caching"
echo -e "   ${RED}✗${NC} Self-evolution"
echo -e "   ${RED}✗${NC} ToolSmith\n"

echo -e "   ${GREEN}✓${NC} P2P mesh networking"
echo -e "   ${GREEN}✓${NC} Thalamus routing"
echo -e "   ${GREEN}✓${NC} WorldModel simulation"
echo -e "   ${GREEN}✓${NC} Basic cognitive loop\n"

echo -e "${BLUE}Happy hacking! 🚀${NC}\n"
