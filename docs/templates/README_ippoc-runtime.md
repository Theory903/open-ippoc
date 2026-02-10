# ippoc-runtime

> Process orchestration, port contracts, and lifecycle management for IPPOC

## Overview

`ippoc-runtime` manages the operational lifecycle of all IPPOC services. It provides supervisor, health monitoring, and port contract enforcement. **No cognition logic lives here** — only execution infrastructure.

## Components

### Supervisor
- `watchdog.py` - Health monitoring and restart policies
- `organism.yaml` - Service configuration and dependencies
- Process lifecycle management

### Ports (Port Contracts)
| Port | Service | Protocol |
|------|---------|----------|
| 8081 | Soma (Identity) | HTTP/gRPC |
| 8001 | Cortex (Cognition) | HTTP |
| 8002 | Body (Execution) | HTTP |
| 8004 | Economy (Tokens) | HTTP |

### Bootstrap
- `genesis.ts` - Initial system bootstrap
- `auth.py` - Authentication configuration

## Usage

```bash
# Start all services
ippoc-runtime start

# Check health
ippoc-runtime status

# Stop gracefully
ippoc-runtime stop

# Restart supervisor
ippoc-runtime restart --force
```

## Configuration

Services are defined in `organism.yaml`:

```yaml
services:
  soma:
    port: 8081
    health_endpoint: /health
    restart_policy: always
    
  cortex:
    port: 8001
    depends_on: [soma]
    health_endpoint: /readyz
```

## Architecture

```
┌─────────────────────────────────────────┐
│           ippoc-runtime                 │
│  ┌─────────────────────────────────┐    │
│  │          Supervisor              │    │
│  │  ┌─────────┐ ┌─────────────┐   │    │
│  │  │Watchdog  │ │LifecycleMgr │   │    │
│  │  └────┬────┘ └──────┬──────┘   │    │
│  └───────┼─────────────┼───────────┘    │
│          │             │               │
│   ┌──────▼──────┐ ┌────▼────────┐     │
│   │  Service A  │ │ Service B    │     │
│   │  (port 8081)│ │ (port 8001)  │     │
│   └─────────────┘ └─────────────┘     │
└─────────────────────────────────────────┘
```

## Requirements

- Python 3.10+
- `pyyaml>=6.0`
- `psutil>=5.9`

## Installation

```bash
pip install ippoc-runtime
```

## Development

```bash
pip install -e .
pytest tests/supervisor/ -v
```
