#!/usr/bin/env bash
#
# IPPOC-OS Quick Start Script
# Automates the entire setup process
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
║                                                           ║
╚═══════════════════════════════════════════════════════════╝
EOF
echo -e "${NC}"

echo -e "${GREEN}Quick Start Script${NC}\n"

# Check prerequisites
echo -e "${YELLOW}[1/6] Checking prerequisites...${NC}"

if ! command -v cargo &> /dev/null; then
    echo -e "${RED}✗ Rust not found. Install from https://rustup.rs${NC}"
    exit 1
fi
echo -e "${GREEN}✓ Rust installed${NC}"

if ! command -v docker &> /dev/null; then
    echo -e "${RED}✗ Docker not found. Install Docker Desktop${NC}"
    exit 1
fi
echo -e "${GREEN}✓ Docker installed${NC}"

if ! command -v pnpm &> /dev/null; then
    echo -e "${YELLOW}⚠ pnpm not found. Installing...${NC}"
    npm install -g pnpm
fi
echo -e "${GREEN}✓ pnpm installed${NC}"

# Start databases
echo -e "\n${YELLOW}[2/6] Starting databases...${NC}"

# Check if containers already exist
if docker ps -a | grep -q ippoc-postgres; then
    echo -e "${YELLOW}Removing existing PostgreSQL container...${NC}"
    docker rm -f ippoc-postgres
fi

if docker ps -a | grep -q ippoc-redis; then
    echo -e "${YELLOW}Removing existing Redis container...${NC}"
    docker rm -f ippoc-redis
fi

docker run -d \
  --name ippoc-postgres \
  -e POSTGRES_PASSWORD=ippoc_secret \
  -e POSTGRES_DB=ippoc_hidb \
  -p 5432:5432 \
  pgvector/pgvector:pg16

docker run -d \
  --name ippoc-redis \
  -p 6379:6379 \
  redis:7-alpine

echo -e "${GREEN}✓ Databases started${NC}"

# Wait for PostgreSQL
echo -e "${YELLOW}Waiting for PostgreSQL to be ready...${NC}"
sleep 8

# Run migrations
echo -e "\n${YELLOW}[3/6] Running database migrations...${NC}"

# Use docker exec to run migrations inside the container
docker exec -i ippoc-postgres psql -U postgres -d ippoc_hidb << 'EOF'
-- Enable pgvector extension
CREATE EXTENSION IF NOT EXISTS vector;
CREATE EXTENSION IF NOT EXISTS "uuid-ossp";

-- Create memories table
CREATE TABLE IF NOT EXISTS memories (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    embedding vector(1536),
    content TEXT NOT NULL,
    confidence REAL DEFAULT 1.0,
    decay_rate REAL DEFAULT 0.1,
    created_at TIMESTAMPTZ DEFAULT NOW(),
    last_accessed TIMESTAMPTZ DEFAULT NOW(),
    source TEXT,
    causal_links UUID[]
);

-- Create index for vector similarity search
CREATE INDEX IF NOT EXISTS memories_embedding_idx ON memories 
USING ivfflat (embedding vector_cosine_ops)
WITH (lists = 100);

-- Create index for confidence-based queries
CREATE INDEX IF NOT EXISTS memories_confidence_idx ON memories (confidence DESC);

-- Create index for time-based queries
CREATE INDEX IF NOT EXISTS memories_created_at_idx ON memories (created_at DESC);
EOF

echo -e "${GREEN}✓ Migrations complete${NC}"

# Build Rust workspace
echo -e "\n${YELLOW}[4/6] Building Rust workspace...${NC}"
cargo build --workspace --release

echo -e "${GREEN}✓ Rust build complete${NC}"

# Build TypeScript apps
echo -e "\n${YELLOW}[5/6] Building TypeScript apps...${NC}"
cd apps/openclaw-cortex
pnpm install
pnpm build
cd ../..

echo -e "${GREEN}✓ TypeScript build complete${NC}"

# Create environment file
echo -e "\n${YELLOW}[6/6] Creating environment file...${NC}"

cat > .env << EOF
# Database connections
DATABASE_URL=postgresql://postgres:ippoc_secret@localhost:5432/ippoc_hidb
REDIS_URL=redis://localhost:6379

# Node configuration
NODE_PORT=9000
NODE_ROLE=reasoning

# LLM configuration (optional)
VLLM_ENDPOINT=http://localhost:8000/v1

# Feature flags
ENABLE_SELF_EVOLUTION=true
ENABLE_TOOLSMITH=true
EOF

echo -e "${GREEN}✓ Environment file created${NC}"

# Success
echo -e "\n${GREEN}╔═══════════════════════════════════════════════════════════╗${NC}"
echo -e "${GREEN}║                                                           ║${NC}"
echo -e "${GREEN}║   ✓ IPPOC-OS Setup Complete!                              ║${NC}"
echo -e "${GREEN}║                                                           ║${NC}"
echo -e "${GREEN}╚═══════════════════════════════════════════════════════════╝${NC}\n"

echo -e "${BLUE}Next steps:${NC}\n"

echo -e "${YELLOW}1. Run IPPOC Node (Terminal 1):${NC}"
echo -e "   ${GREEN}source .env && cargo run --release --bin ippoc-node -- --port 9000${NC}\n"

echo -e "${YELLOW}2. Run OpenClaw Cortex (Terminal 2):${NC}"
echo -e "   ${GREEN}cd apps/openclaw-cortex && source ../../.env && pnpm start${NC}\n"

echo -e "${YELLOW}3. Test the system:${NC}"
echo -e "   ${GREEN}curl http://localhost:9000/status${NC}\n"

echo -e "${BLUE}Documentation:${NC}"
echo -e "   - Quick Start: ${GREEN}docs/QUICKSTART.md${NC}"
echo -e "   - Capabilities: ${GREEN}CAPABILITIES.md${NC}"
echo -e "   - Architecture: ${GREEN}DOC.md${NC}\n"

echo -e "${YELLOW}To stop databases:${NC}"
echo -e "   ${GREEN}docker stop ippoc-postgres ippoc-redis${NC}\n"

echo -e "${BLUE}Happy hacking! 🚀${NC}\n"
