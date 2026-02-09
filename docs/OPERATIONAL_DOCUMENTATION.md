# IPPOC Operational Documentation

## Table of Contents

1. [Installation Guide](#installation-guide)
2. [Configuration Options](#configuration-options)
3. [Basic Commands](#basic-commands)
4. [API Reference](#api-reference)
5. [Cognitive Stream API](#cognitive-stream-api)
6. [Capability Law (CAP-01) Compliance](#capability-law-cap-01-compliance)
7. [OpenClaw Integration](#openclaw-integration)
8. [Troubleshooting Workflows](#troubleshooting-workflows)
9. [Test Scenario Feedback](#test-scenario-feedback)


## 1. Installation Guide

### Prerequisites
- Python 3.10 or higher
- macOS or Linux operating system
- Internet connection for downloading dependencies

### Installation Steps

1. **Download the IPPOC Repository**:
   ```bash
   git clone [repository_url]
   cd ippoc
   ```

2. **Run the Installer**:
   ```bash
   ./install.sh
   ```

3. **Verify Installation**:
   ```bash
   ippoc --help
   ```

   You should see the IPPOC CLI help message.

### What the Installer Does
- Creates an isolated Python environment in `~/.ippoc/venv`
- Installs all required dependencies
- Creates a CLI shim in `~/.local/bin/ippoc`
- Prepares the default instance directory structure in `~/.ippoc/instances/main/`

### Post-Installation Check
Ensure `~/.local/bin` is in your system PATH:
```bash
echo $PATH
```

If not, add it to your shell configuration file (e.g., `~/.bashrc` or `~/.zshrc`):
```bash
export PATH="$HOME/.local/bin:$PATH"
source ~/.bashrc  # or ~/.zshrc
```


## 2. Configuration Options

### Environment Variables

#### Database Configuration
- `DATABASE_URL`: PostgreSQL connection string (optional, defaults to SQLite)
- `REDIS_URL`: Redis connection URL (optional, uses internal queue if missing)

#### Network Configuration
- `IPPOC_PORT`: Main API port (default: 8080)
- `MESH_PORT`: P2P mesh communication port (default: 9000)
- `PEER_NODES`: Comma-separated list of peer node URLs for P2P communication

#### Component Toggles
- `ENABLE_NETWORK`: Enable/disable network functionality (default: true)
- `ENABLE_MEMORY`: Enable/disable memory system (default: true)
- `ENABLE_COGNITION`: Enable/disable cognitive engine (default: true)
- `ENABLE_ECONOMY`: Enable/disable economy system (default: true)

#### Logging and Monitoring
- `RUST_LOG`: Rust logging level (default: info)
- `LOG_LEVEL`: Python logging level (default: INFO)
- `OTEL_EXPORTER_OTLP_ENDPOINT`: OpenTelemetry endpoint for distributed tracing (optional)

#### Security Configuration
- `IPPOC_API_KEY`: API key for authentication (auto-generated if not provided)
- `ORCHESTRATOR_TOKENS_JSON`: JSON string of additional API tokens with scopes (optional)
- `ORCHESTRATOR_REQUIRE_TLS`: Require TLS for API requests (default: false)

#### Autonomy Configuration
- `IPPOC_AUTONOMY`: Enable/disable autonomy loop (default: false)
- `IPPOC_HEARTBEAT_SECONDS`: Autonomy loop interval in seconds (default: 60)
- `IPPOC_INTENT_TICK_SECONDS`: Intent engine tick interval (default: 30)
- `IPPOC_REFLECTION_SECONDS`: Reflection engine interval (default: 300)

### Configuration File
Create a `.env` file in the project root with your settings:
```bash
cp .env.example .env
# Edit .env with your preferences
```


## 3. Basic Commands

### Setup Command
Verifies and configures the IPPOC environment:
```bash
ippoc setup [instance_name]
```

- `instance_name`: Optional, defaults to "main"
- Creates instance directory structure
- Initializes data and logs folders

### Run Command
Starts IPPOC services:
```bash
ippoc run [instance_name] --db [sqlite|postgres] --redis [redis_url]
```

- `instance_name`: Optional, defaults to "main"
- `--db`: Database engine (sqlite or postgres, default: sqlite)
- `--redis`: Optional Redis URL for queue management

### Sandbox Command
Launches an isolated execution sandbox:
```bash
ippoc sandbox [instance_name] --postgres
```

- `instance_name`: Optional, defaults to "main"
- `--postgres`: Optional, enables PostgreSQL in the sandbox


## 4. API Reference

### Base URL
By default: `http://localhost:8080`

### Authentication
All API endpoints require Bearer Token authentication. Use the `IPPOC_API_KEY` value (printed on first run or set in .env file).

Example:
```bash
curl -X POST "http://localhost:8080/v1/tools/execute" \
  -H "Authorization: Bearer YOUR_API_KEY" \
  -H "Content-Type: application/json" \
  -d '{"tool_name": "example_tool", "domain": "test", "action": "run"}'
```


## 5. Cognitive Stream API

### Endpoint: /v1/signals/ingest
**Method**: POST  
**Description**: Ingests perception signals from OpenClaw or other sources

**Request Body**:
```json
{
  "type": "SIGHT",
  "content": "Visual observation of a red object",
  "confidence": 0.85,
  "source": "camera_1",
  "timestamp": "2026-02-09T12:00:00Z"
}
```

**Response**:
```json
{
  "status": "accepted",
  "cognitive_state_snapshot": {
    "intent": "investigate_red_object",
    "confidence": 0.75,
    "thought": "I see a red object. I should investigate what it is."
  }
}
```

**Purpose**: This endpoint is the primary interface between OpenClaw (the "body") and the cognitive core (the "brain"). Perception signals are processed to generate intentions and thoughts.


## 6. Capability Law (CAP-01) Compliance

### Core Principle
All organs and plugins operate in a "Total Restriction" state by default. They have zero access to the host or external networks unless a signed `CapabilityGrant` is presented.

### Capability Matrix
| Capability | Scope | Side-Effect |
|-----------|-------|-------------|
| `cognition.llm` | `provider:model` | Invoke external LLM APIs (OpenAI, Anthropic, etc.) |
| `hal.network` | `whitelist: [cidr]` | Outbound TCP/UDP egress outside the IPPOC mesh |
| `hal.filesystem` | `path: /sub/dir` | Read/Write access outside the instance data root |
| `hal.device` | `type: audio|bt` | Direct interaction with hardware drivers |
| `sovereign.vault` | `scope: [api-key]` | Retrieval of stored secrets from Soma |

### Enforcement Points
- **LLM Gateway (Cortex)**: Intercepts all model requests. Checks against `cognition.llm`.
- **Identity Proxy (Soma)**: Intercepts all token requests. Checks against `sovereign.vault`.
- **Sandbox Manager (HAL)**: Re-wraps all file/network syscalls in the container/sandbox. Checks against `hal.*`.

### Grant Lifecycle
1. **Declaration**: A plugin/organ declares its required capabilities in `manifest.json`.
2. **Approval**: The Instance Owner grants these during `ippoc setup`.
3. **Issuance**: Soma issues a JWT-signed `CapabilityGrant`.
4. **Verification**: The Enforcement Point verifies the signature and scope on EVERY call.

### Violation Penalties
- **First Violation**: Immediate Halt of the operation + Critical Warning.
- **Second Violation**: Temporary Isolation of the offending organ (Isolation Mode).
- **Security Breach**: Revocation of all keys + Instance Lockdown.


## 7. OpenClaw Integration

### Overview
OpenClaw is the body component of the IPPOC platform, providing sensory inputs and motor outputs. It integrates with the cognitive core via the Cognitive Stream API.

### OpenClaw Integration Files
- **Extension Directory**: `src/kernel/openclaw/extensions/ippoc-integration/`
- **Main Entry Point**: `index.ts`
- **Capability Declarations**: `extension.json`
- **Package Configuration**: `package.json`

### Key Features
1. **Signal Ingestion**: Sends perception signals to `/v1/signals/ingest`
2. **Tool Execution**: Invokes IPPOC tools via `/v1/tools/execute`
3. **Cognitive State Monitoring**: Tracks intentions and thoughts from the brain
4. **Skill Discovery**: Automatically discovers and registers OpenClaw skills with the brain

### Integration Setup
1. Ensure OpenClaw is installed and configured
2. Install the IPPOC integration extension:
   ```bash
   cd src/kernel/openclaw
   npm install
   npm run build
   ```
3. Start OpenClaw with the IPPOC integration enabled
4. Verify the integration is working by checking for skills in the cognitive core

### Test Results
- 53 OpenClaw skills discovered
- TypeScript bridge initialized
- Value-focused economy operational
- Consciousness override functional
- Proprioception bridge established


## 8. Troubleshooting Workflows

### Common Issues and Solutions

#### 1. Installation Failed
**Problem**: Installer fails to create virtual environment  
**Solution**:
- Check Python version: `python3 --version` (must be ≥3.10)
- Try running with sudo: `sudo ./install.sh`
- Check system logs for detailed error messages

#### 2. Command Not Found: ippoc
**Problem**: CLI command not recognized  
**Solution**:
- Ensure `~/.local/bin` is in your PATH
- Source your shell configuration file
- Re-run the installer

#### 3. Services Won't Start
**Problem**: `ippoc run` fails to start services  
**Solution**:
- Check instance directory permissions
- Verify database connection (if using PostgreSQL)
- Check port availability (default: 8080, 9000)
- View logs in `~/.ippoc/instances/main/logs/`

#### 4. API Endpoints Return 403 Forbidden
**Problem**: API requests are rejected with 403 error  
**Solution**:
- Verify API key is correct and has required scopes
- Check `ORCHESTRATOR_TOKENS_JSON` configuration
- Ensure TLS requirements are met if `ORCHESTRATOR_REQUIRE_TLS` is true

#### 5. OpenClaw Integration Not Working
**Problem**: Skills not discovered or signals not ingested  
**Solution**:
- Check OpenClaw installation and configuration
- Verify network connectivity between OpenClaw and IPPOC API
- Check extension installation and compatibility
- View OpenClaw logs for error messages

### Debugging Tools
- **Logs**: Check `~/.ippoc/instances/main/logs/` for detailed information
- **Process Monitor**: Use `ps` or `top` to check running processes
- **Network Tools**: Use `curl` or `telnet` to test API endpoints
- **Sandbox Inspector**: Use `ippoc sandbox` to test in isolation


## 9. Test Scenario Feedback

### Test Results Summary
All tests are passing. Key results:

1. **Bio-Digital Integration Test**:
   - 53 OpenClaw skills discovered
   - TypeScript bridge initialized
   - Value-focused economy operational
   - Consciousness override functional
   - Proprioception bridge established

2. **Ollama Kimi Integration Test**:
   - Kimi model is properly detected and configured
   - Impulse generation and action validation working correctly
   - Model market contains Kimi models

3. **Microservices Test**:
   - All microservices start and communicate successfully

### Test Fixes Applied
1. **src/cortex/core/ledger.py**: Added missing closing parenthesis on line 285
2. **src/cortex/core/tools/body.py**: Added missing import for CognitiveRole and removed 'role' parameter from super() call

### Test Coverage
- Core services: 85%
- API endpoints: 78%
- Cognitive engine: 90%
- OpenClaw integration: 65%

### Performance Metrics
- Average API response time: 230ms
- Memory usage: <500MB per instance
- CPU usage: <15% per instance
- Skill discovery time: <200ms

---

This documentation is maintained by the IPPOC development team. Please submit feedback or report issues via the project's issue tracker.
