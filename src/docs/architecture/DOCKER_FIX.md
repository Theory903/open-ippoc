# Docker Not Running - Quick Fix

## Problem

Docker Desktop is not running. You saw this error:
```
Cannot connect to the Docker daemon at unix:///Users/abhishekjha/.docker/run/docker.sock
```

## Solutions

### Option 1: Start Docker Desktop (Recommended)

1. **Open Docker Desktop** from Applications
2. **Wait** for it to fully start (whale icon in menu bar)
3. **Run setup again**:
   ```bash
   ./tools/quickstart.sh
   ```

---

### Option 2: Run Without Docker (Limited Features)

If you don't want to use Docker, run the no-Docker version:

```bash
./tools/quickstart-no-docker.sh
```

**What works:**
- ✅ P2P mesh networking
- ✅ Thalamus routing
- ✅ WorldModel simulation
- ✅ Basic cognitive loop

**What doesn't work:**
- ❌ HiDB memory storage (no PostgreSQL)
- ❌ Redis caching
- ❌ Self-evolution (needs database)
- ❌ ToolSmith (needs database)

---

### Option 3: Install PostgreSQL & Redis Locally

**macOS (Homebrew):**
```bash
# Install
brew install postgresql@16 redis

# Start services
brew services start postgresql@16
brew services start redis

# Create database
createdb ippoc_hidb

# Install pgvector
cd /opt/homebrew/opt/postgresql@16
git clone https://github.com/pgvector/pgvector.git
cd pgvector
make
make install

# Run migrations
psql ippoc_hidb -f /Users/abhishekjha/Downloads/ippoc/libs/hidb/migrations/001_init.sql

# Update .env
cat > .env << EOF
DATABASE_URL=postgresql://$(whoami)@localhost:5432/ippoc_hidb
REDIS_URL=redis://localhost:6379
NODE_PORT=9000
NODE_ROLE=reasoning
ENABLE_SELF_EVOLUTION=true
ENABLE_TOOLSMITH=true
EOF

# Build and run
cargo build --workspace --release
cargo run --release --bin ippoc-node -- --port 9000
```

---

## Quick Decision Matrix

| Scenario | Recommended Solution |
|----------|---------------------|
| **Have Docker Desktop** | Start it, run `./tools/quickstart.sh` |
| **No Docker, want full features** | Option 3 (local install) |
| **Just want to test** | Option 2 (no-Docker version) |
| **Production deployment** | Use Docker or Kubernetes |

---

## Next Steps

**After choosing an option:**

1. **Build** (if not done):
   ```bash
   cargo build --workspace --release
   ```

2. **Run Node** (Terminal 1):
   ```bash
   source .env
   cargo run --release --bin ippoc-node -- --port 9000
   ```

3. **Run Cortex** (Terminal 2):
   ```bash
   cd apps/openclaw-cortex
   source ../../.env
   pnpm start
   ```

---

**Need help?** Check [QUICKSTART.md](file:///Users/abhishekjha/.gemini/antigravity/brain/9c372563-1aac-45ed-8e24-13d3411ebd6b/QUICKSTART.md) for detailed troubleshooting.
