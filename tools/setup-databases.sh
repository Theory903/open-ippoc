#!/usr/bin/env bash
#
# Manual Database Setup
# Run this if quickstart.sh fails
#

set -euo pipefail

echo "=== IPPOC-OS Manual Database Setup ==="
echo ""

# Step 1: Clean up existing containers
echo "[1/4] Cleaning up existing containers..."
docker stop ippoc-postgres ippoc-redis 2>/dev/null || true
docker rm ippoc-postgres ippoc-redis 2>/dev/null || true
echo "✓ Cleanup complete"

# Step 2: Start fresh containers
echo ""
echo "[2/4] Starting fresh database containers..."
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

echo "✓ Containers started"

# Step 3: Wait and run migrations
echo ""
echo "[3/4] Waiting for PostgreSQL (10 seconds)..."
sleep 10

echo "Running migrations..."
docker exec -i ippoc-postgres psql -U postgres -d ippoc_hidb << 'EOF'
CREATE EXTENSION IF NOT EXISTS vector;
CREATE EXTENSION IF NOT EXISTS "uuid-ossp";

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

CREATE INDEX IF NOT EXISTS memories_embedding_idx ON memories 
USING ivfflat (embedding vector_cosine_ops)
WITH (lists = 100);

CREATE INDEX IF NOT EXISTS memories_confidence_idx ON memories (confidence DESC);
CREATE INDEX IF NOT EXISTS memories_created_at_idx ON memories (created_at DESC);
EOF

echo "✓ Migrations complete"

# Step 4: Create .env file
echo ""
echo "[4/4] Creating .env file..."
cat > .env << 'EOF'
DATABASE_URL=postgresql://postgres:ippoc_secret@localhost:5432/ippoc_hidb
REDIS_URL=redis://localhost:6379
NODE_PORT=9000
NODE_ROLE=reasoning
ENABLE_SELF_EVOLUTION=true
ENABLE_TOOLSMITH=true
EOF

echo "✓ Environment file created"

echo ""
echo "=== Setup Complete! ==="
echo ""
echo "Databases are ready. Now run:"
echo ""
echo "  # Build (if not done)"
echo "  cargo build --workspace --release"
echo ""
echo "  # Run node (Terminal 1)"
echo "  source .env && cargo run --release --bin ippoc-node -- --port 9000"
echo ""
echo "  # Run cortex (Terminal 2)"
echo "  cd apps/openclaw-cortex && source ../../.env && pnpm start"
echo ""
