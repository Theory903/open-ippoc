# OpenClaw + IPPOC Local Installation & Validation Guide

## Overview

This guide provides a detailed, step-by-step process for installing, configuring, and validating the OpenClaw AI Assistant with IPPOC (Integrated Perception, Planning, and Control) architecture on your local machine. The installation supports both Docker and manual setups.

## System Requirements

### Minimum Configuration
- **OS**: macOS 10.15+, Ubuntu 20.04+, Windows 10/11 (WSL2 recommended)
- **CPU**: 4 cores (6 cores recommended)
- **RAM**: 16 GB (32 GB recommended)
- **Storage**: 50 GB free space (SSD recommended)
- **Network**: Stable internet connection for dependencies

## Prerequisites

### 1. Install Docker (Recommended for Easy Setup)
**Docker Desktop**: https://www.docker.com/products/docker-desktop/

**Verify Installation**:
```bash
docker --version
docker-compose --version
```

### 2. Install Git
```bash
# macOS (Homebrew)
brew install git

# Ubuntu/Debian
sudo apt update && sudo apt install git -y

# Windows (Chocolatey)
choco install git
```

**Verify**:
```bash
git --version
```

### 3. Install Node.js & npm (for OpenClaw Cortex)
**Node.js 18+**: https://nodejs.org/

**Verify**:
```bash
node --version
npm --version
```

### 4. Install Rust (for Body/Mesh Services)
```bash
# All platforms
curl --proto '=https' --tlsv1.2 -sSf https://sh.rustup.rs | sh
```

**Verify**:
```bash
rustc --version
cargo --version
```

## Installation & Configuration

### Option 1: Docker Compose (Recommended for Beginners)

#### Step 1: Clone the Repository
```bash
git clone https://github.com/your-username/ippoc.git
cd ippoc
```

#### Step 2: Configure Environment Variables
Create a `.env` file in the root directory:
```bash
cat > .env << EOF
# Database
POSTGRES_PASSWORD=ippoc_secret
DATABASE_URL=postgresql://postgres:ippoc_secret@postgres:5432/ippoc_hidb

# Redis
REDIS_URL=redis://redis:6379

# Body Service
NODE_PORT=8080
NODE_ROLE=reasoning
ENABLE_SELF_EVOLUTION=true
ENABLE_TOOLSMITH=true

# Memory Service
GOOGLE_API_KEY=your_google_api_key_here

# OpenClaw Cortex
ENABLE_ECONOMY=true
WALLET_PATH=./wallet.json
REPUTATION_THRESHOLD=80

# VLLM (Optional)
VLLM_ENDPOINT=http://localhost:8000/v1
EOF
```

#### Step 3: Build and Start Services
```bash
# Build all Docker images
docker-compose -f deploy/docker-compose.prod.yml build

# Start all services in detached mode
docker-compose -f deploy/docker-compose.prod.yml up -d
```

#### Step 4: Verify Services Are Running
```bash
# Check container status
docker-compose -f deploy/docker-compose.prod.yml ps

# View logs
docker-compose -f deploy/docker-compose.prod.yml logs -f
```

#### Expected Services:
- `ippoc-node`: Rust body service (port 8080)
- `ippoc-memory`: Python memory service (port 3001)
- `ippoc-cortex`: Python reasoning service (port 8000)
- `openclaw-cortex`: TypeScript AI assistant (port 3000)
- `postgres`: Database (port 5432)
- `redis`: Cache (port 6379)
- `ippoc-gateway`: Nginx reverse proxy (port 80)

### Option 2: Manual Installation (For Development)

#### Step 1: Database Setup
**PostgreSQL (14+)**:
```bash
# macOS (Homebrew)
brew install postgresql@14
brew services start postgresql@14
createdb ippoc_hidb
createuser -s postgres

# Ubuntu/Debian
sudo apt install postgresql-14
sudo systemctl start postgresql
sudo -u postgres createdb ippoc_hidb
```

**Redis (6+)**:
```bash
# macOS
brew install redis
brew services start redis

# Ubuntu/Debian
sudo apt install redis-server
sudo systemctl start redis
```

#### Step 2: Memory Service
```bash
cd memory
pip install -r requirements.txt
python api/server.py
```

**Verify**: Open http://localhost:3001/health

#### Step 3: Body Service
```bash
cd body
cargo build
cargo run
```

**Verify**: Open http://localhost:8080/v1/health

#### Step 4: Brain Service
```bash
cd brain
pip install -r requirements.txt
python cortex/server.py
```

**Verify**: Open http://localhost:8000/v1/health

#### Step 5: OpenClaw Cortex
```bash
cd brain/cortex/openclaw-cortex
npm install
npm start
```

**Verify**: Open http://localhost:3000/health

## Configuration Validation

### 1. API Health Checks
```bash
# Body Service
curl -X GET http://localhost:8080/v1/health

# Memory Service
curl -X GET http://localhost:3001/health

# Brain Service
curl -X GET http://localhost:8000/v1/health

# OpenClaw Cortex
curl -X GET http://localhost:3000/health
```

### 2. Test Data Storage
```bash
# Store an event
curl -X POST http://localhost:3001/api/v1/events \
  -H "Content-Type: application/json" \
  -d '{
    "text": "Test event from OpenClaw",
    "embedding": [0.1, 0.2, 0.3],
    "timestamp": 1700000000,
    "metadata": {"source": "test"}
  }'

# Get events
curl -X GET "http://localhost:3001/api/v1/events?limit=5"
```

### 3. Code Execution Test
```bash
curl -X POST http://localhost:8080/v1/execute \
  -H "Content-Type: application/json" \
  -d '{
    "workload_id": "test-workload-1",
    "function_name": "main",
    "args": []
  }'
```

## UI-Based Testing

### Mind TUI (Terminal Interface)
```bash
cd mind/tui
cargo run
```

**Features to Test**:
1. **Wallet Management**: Check balance and transaction history
2. **Mesh Visualization**: View connected peers
3. **Agent Control**: Start/stop cognitive agents
4. **Code Execution**: Run and simulate code
5. **System Monitoring**: Check CPU, memory, and network usage

### Web Interface (OpenClaw Dashboard)
**URL**: http://localhost:3000

**Features to Test**:
1. **Thalamus Dashboard**: View signal routing statistics
2. **WebLearner**: Test search functionality
3. **ToolSmith**: Discover and install tools
4. **GitEvolution**: Test evolution simulation
5. **Economy**: Check balance and reputation

## Network & Port Configuration

### Port Mapping
| Service | Port | Protocol |
|---------|------|----------|
| Nginx Gateway | 80/443 | HTTP/HTTPS |
| OpenClaw Cortex | 3000 | HTTP |
| Body Service | 8080 | HTTP |
| Brain Service | 8000 | HTTP |
| Memory Service | 3001 | HTTP |
| PostgreSQL | 5432 | TCP |
| Redis | 6379 | TCP |
| VLLM (Optional) | 8000 | HTTP |

### Firewall Configuration
```bash
# macOS
sudo /usr/libexec/ApplicationFirewall/socketfilterfw --add /Applications/Docker.app
sudo /usr/libexec/ApplicationFirewall/socketfilterfw --unblockapp /Applications/Docker.app

# Ubuntu/Debian
sudo ufw allow 80
sudo ufw allow 443
sudo ufw allow 3000
sudo ufw allow 8080
sudo ufw allow 8000
sudo ufw allow 3001
sudo ufw allow 5432
sudo ufw allow 6379
```

## Troubleshooting

### Common Issues & Solutions

#### 1. Docker Container Won't Start
```bash
# Check logs
docker-compose -f deploy/docker-compose.prod.yml logs <service-name>

# Recreate container
docker-compose -f deploy/docker-compose.prod.yml up -d --force-recreate <service-name>

# Check resource usage
docker stats
```

#### 2. Database Connection Errors
```bash
# Verify PostgreSQL is running
psql -h localhost -U postgres -d ippoc_hidb -c "SELECT 1;"

# Check if migrations ran
cd memory
python -m pytest tests/test_integration.py -v
```

#### 3. Memory Service Failures
```bash
# Check Redis connection
redis-cli ping

# Check database tables exist
psql -h localhost -U postgres -d ippoc_hidb -c "\dt"
```

#### 4. Body Service Compilation Errors
```bash
# Clean and rebuild
cd body
cargo clean
cargo build

# Check Rust version
rustc --version
```

#### 5. OpenClaw Cortex Issues
```bash
# Check dependencies
cd brain/cortex/openclaw-cortex
npm install

# Check TypeScript compilation
npm run build

# Check port availability
lsof -ti :3000 | xargs kill -9 2>/dev/null || true
```

#### 6. VLLM Connection Errors
```bash
# Verify VLLM is running
curl -X GET http://localhost:8000/v1/models

# Check VLLM logs
cd body/scripts
cat vllm_service.sh
```

## Advanced Configuration

### Enabling GPU Support for VLLM
```bash
# Update Docker Compose
vi deploy/docker-compose.prod.yml

# Add GPU configuration
vllm:
  deploy:
    resources:
      reservations:
        devices:
          - driver: nvidia
            count: 1
            capabilities: [gpu]

# Restart VLLM service
docker-compose -f deploy/docker-compose.prod.yml up -d --force-recreate vllm
```

### Customizing Cognitive Agents
```bash
# Modify agent configuration
vi brain/cortex/openclaw-cortex/src/ippoc-config.ts

# Restart OpenClaw Cortex
cd brain/cortex/openclaw-cortex
npm restart
```

### Adding Custom Tools
```bash
# Create tool file
vi brain/cortex/openclaw-cortex/src/agents/tools/my-tool.ts

# Register with ToolSmith
cd brain/cortex/openclaw-cortex
npm run build
```

## Performance Optimization

### 1. Resource Limits
```bash
# Docker resource allocation
# Docker Desktop > Settings > Resources > Advanced
- CPUs: 6-8
- Memory: 24 GB
- Swap: 4 GB
- Disk: 100 GB
```

### 2. Database Tuning
```bash
# PostgreSQL configuration
vi /usr/local/var/postgres/postgresql.conf

max_connections = 200
shared_buffers = 2GB
work_mem = 64MB
maintenance_work_mem = 256MB
```

### 3. Redis Configuration
```bash
# Redis configuration
vi /usr/local/etc/redis.conf

maxmemory 2gb
maxmemory-policy allkeys-lru
```

## Cleanup & Uninstallation

### Docker Cleanup
```bash
# Stop all services
docker-compose -f deploy/docker-compose.prod.yml down

# Remove containers, networks, and volumes
docker-compose -f deploy/docker-compose.prod.yml down -v

# Remove images
docker rmi $(docker images 'ippoc*' -q)
```

### Manual Cleanup
```bash
# Stop services
pkill -f "python.*server"
pkill -f "cargo run"

# Clean Rust build artifacts
cd body && cargo clean

# Clean npm dependencies
cd brain/cortex/openclaw-cortex && rm -rf node_modules package-lock.json

# Drop database
dropdb ippoc_hidb
```

## Validation Checklist

### Core Functionality
- [ ] Docker containers start successfully
- [ ] All API endpoints respond with 200 OK
- [ ] Data is stored and retrieved from HiDB
- [ ] Code execution works
- [ ] Cognitive agents respond
- [ ] Economy operations function
- [ ] Mesh communication is established

### UI Testing
- [ ] Mind TUI loads and functions
- [ ] OpenClaw dashboard displays data
- [ ] Agent controls work
- [ ] Search functionality works
- [ ] Code simulation works

### Performance
- [ ] Response times are <30ms (reflex), <300ms (habit), <5000ms (cognitive)
- [ ] Memory usage is reasonable
- [ ] Network connections are stable

## Next Steps

1. **Customize Configuration**: Adjust settings in `.env` and `ippoc-config.ts`
2. **Add Custom Tools**: Extend the system with your own tools
3. **Train Models**: Fine-tune language models
4. **Deploy to Cloud**: Use Kubernetes manifests for production
5. **Join Testnet**: Connect to the IPPOC testnet for distributed testing

## Support

For assistance:
- Check the documentation in `/docs`
- Look at PRD specifications in `/docs/prds`
- Review logs in `/logs`
- Create an issue in the GitHub repository

---

**Version**: 1.0  
**Last Updated**: 2024-01-01  
**Maintainers**: OpenClaw Team