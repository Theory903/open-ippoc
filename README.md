# IPPOC-OS: The Sovereign Cognitive Operating System

> **"IPPOC stands on its own, and integrates by choice."**

IPPOC-OS is a self-contained, agentic platform designed for structural, runtime, and cognitive independence. It operates by constitutional law (CAP-01), ensuring safety and sovereignty for the operator.

---

## 🚀 Quick Start (v0.9.0-stable)

### Prerequisites

- Python 3.10+
- pip or conda
- 4GB RAM minimum
- 1GB disk space

### 1. Install

Install the IPPOC platform into an isolated environment:

```bash
# Clone the repository
git clone https://github.com/your-org/ippoc.git
cd ippoc

# Install in development mode
pip install -e .

# Or run the universal installer
./install.sh
```

### 2. Run

Start all core cognitive services:

```bash
ippoc run
```

This starts:
- **Soma** (Identity & Trust) on port 8081
- **Cortex** (Cognition & Tools) on port 8000

### 3. Verify

Check that all services are healthy:

```bash
ippoc status
```

Expected output:
```json
{
  "soma": "healthy",
  "cortex": "ready",
  "tools_loaded": 10
}
```

---

## 🏗️ Architecture

### Core Services

| Service | Port | Purpose |
|---------|------|---------|
| **Soma** | 8081 | Identity, Trust, Authentication, Memory |
| **Cortex** | 8000 | Cognition, Tool Execution, Orchestration |

### Design Principles

1. **Sovereign Engine**: Decoupled cognition that does not require an external control plane
2. **Law-Governed (CAP-01)**: Hard-coded capability boundaries that cannot be bypassed by prompts
3. **Plugin Registry**: Isolated embodiment (e.g., OpenClaw) that loads only by explicit choice
4. **Immutable Ledger**: Cryptographically verifiable record of all cognitive actions and violations

### Startup Sequence

```
1. Check ports 8081 and 8000 availability
2. Start Soma (Identity & Trust)
3. Wait for Soma health check (/v1/system/diagnostics)
4. Issue API key from Soma (/v1/auth/issue)
5. Start Cortex (Cognition & Tools)
6. Wait for Cortex readiness (/readyz)
7. Monitor services until shutdown
```

---

## 📖 CLI Reference

### Core Commands

```bash
# Start all services
ippoc run [instance] [--db sqlite|postgres] [--redis url]

# Check system status
ippoc status

# Verify environment
ippoc setup [instance]
```

### Cognitive Operations

```bash
# List active intents
ippoc intents

# Stream cognitive thoughts
ippoc thoughts [--tail]

# Explain execution
ippoc explain [execution_id|latest]
```

### Signal Ingestion

```bash
# Ingest sensory signals
ippoc signal ingest SIGHT "User showed me a document"
ippoc signal ingest HEARING "User asked about weather"
ippoc signal ingest TOUCH "User pressed a button"
ippoc signal ingest SMELL "Detected coffee aroma"
ippoc signal ingest TASTE "Flavor profile: sweet"
```

### System Control

```bash
# Control autonomy
ippoc autonomy on    # Full autonomous operation
ippoc autonomy off   # Human approval required
ippoc autonomy pause # Temporary halt

# View violations
ippoc violations
```

---

## 🔧 Configuration

### Environment Variables

| Variable | Default | Description |
|----------|---------|-------------|
| `IPPOC_BASE_DIR` | `~/.ippoc` | Base directory for data and logs |
| `IPPOC_SOMA_URL` | `http://localhost:8081` | Soma service URL |
| `IPPOC_CORTEX_URL` | `http://localhost:8000` | Cortex service URL |
| `IPPOC_API_KEY` | - | API key for authentication |
| `IPPOC_PRODUCTION` | `false` | Enable production mode |
| `DEV_MODE` | `false` | Development mode with default keys |
| `IPPOC_DATABASE_TYPE` | `sqlite` | Database backend |
| `IPPOC_REDIS_URL` | - | Redis URL for task queue |

### Instance Structure

```
~/.ippoc/
└── instances/
    └── main/
        ├── data/
        │   ├── cortex.db
        │   └── ledger.db
        └── logs/
            ├── soma.log
            └── cortex.log
```

---

## 🛠️ Available Tools

Cortex includes 10 integrated tools:

| Tool | Purpose |
|------|---------|
| **memory** | Persistent memory storage and retrieval |
| **body** | System health and monitoring |
| **evolution** | Self-improvement and code updates |
| **cerebellum** | Motor coordination and execution |
| **simulation** | What-if scenario modeling |
| **social** | Communication and interaction |
| **maintainer** | System maintenance tasks |
| **economy** | Resource allocation and costing |
| **earnings** | Performance tracking |
| **native_shell** | Direct shell command execution |

---

## 🚨 Troubleshooting

### Port Already in Use

```bash
# Check what's using the port
lsof -i :8000
lsof -i :8081

# Kill existing processes
lsof -ti :8000 | xargs kill -9
lsof -ti :8081 | xargs kill -9

# Or use the cleanup script
./kill_existing_processes.sh
```

### Services Not Starting

```bash
# Check logs
cat ~/.ippoc/instances/main/logs/soma.log
cat ~/.ippoc/instances/main/logs/cortex.log

# Manual health check
curl http://localhost:8081/v1/system/diagnostics
curl http://localhost:8000/healthz
```

### API Key Issues

```bash
# Set API key manually
export IPPOC_API_KEY="your-key-here"

# Or enable dev mode
export DEV_MODE=true
```

### Full Reset

```bash
# Kill all processes
./kill_existing_processes.sh

# Clear data (optional)
rm -rf ~/.ippoc/instances/main/data/*

# Restart
ippoc run
```

---

## 📚 Documentation

| Document | Description |
|----------|-------------|
| [Independence Manifest](docs/INDEPENDENCE.md) | Philosophy of operator sovereignty |
| [Trust Chain Attestation](TRUST_CHAIN.md) | Cryptographic trust verification |
| [Security & Threat Model](SECURITY.md) | Security architecture and threats |
| [Hostile Review Protocol](docs/HOSTILE_REVIEW_PROTOCOL.md) | Adversarial testing procedures |
| [Capability Law](CAPABILITY_LAW.md) | CAP-01 constitutional boundaries |
| [Supervision Rules](SUPERVISION_RULES.md) | Operational oversight guidelines |

---

## 🔐 Security

IPPOC operates under **CAP-01** (Capability Law), which enforces:

1. **No External Dependencies**: All cognition is local
2. **Hard Boundaries**: Capability limits cannot be overridden
3. **Audit Trail**: All actions are logged immutably
4. **Operator Sovereignty**: The operator retains ultimate control

---

## 📝 API Reference

### Soma API (Port 8081)

```bash
# Health check
GET /health
GET /v1/system/diagnostics

# Authentication
POST /v1/auth/issue
GET /v1/auth/verify

# Memory
GET /v1/memory/recent?limit=20

# Identity
POST /v1/identity/register
GET /v1/identity/trust/{node_id}
```

### Cortex API (Port 8000)

```bash
# Health
GET /healthz
GET /readyz

# Cognitive
POST /v1/signals/ingest
GET /v1/intents/list
GET /v1/cognitive/stream

# Execution
GET /v1/orchestrator/explain/{id}

# System
GET /v1/system/violations
POST /v1/system/autonomy/control
```

---

## 🤝 Contributing

1. Fork the repository
2. Create a feature branch
3. Run tests: `pytest tests/`
4. Submit a pull request

All contributions must pass the hostile review protocol.

---

## 📄 License

MIT License - See LICENSE file for details.

---

**Status: v0.9.0-stable | Released & Verified**

*IPPOC stands on its own, and integrates by choice.*
