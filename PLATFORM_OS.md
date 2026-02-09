# IPPOC PLATFORM OS
**STATUS: IMMUTABLE LAW v1.0.0**
*Any change requires a version bump and justification.*

## 1. Prime Directives
IPPOC is a sovereign cognitive operating surface. This document defines the non-negotiable laws governing its execution, isolation, and capability enforcement.

## 0. Instance Model (Foundational)

IPPOC supports multiple isolated instances. An "instance" is a sovereign cluster of cognitive organs.

### Path Structure
Every instance is rooted at:
`~/.ippoc/instances/<name>/`
  ├── `venv/`         # Isolated Python runtime
  ├── `data/`         # SQLite DBs, secrets, HiDB
  ├── `logs/`         # Redirected service logs
  └── `config.toml`  # Instance-specific overrides

### Identity & Tenancy
- **Default Instance**: `main`.
- **Isolation**: Processes from `instance:alpha` can never access file-descriptors or sockets of `instance:beta`.
- **Command**: `ippoc run <name>` (Defaults to `main`).

## 1. Capability Enforcement Gate

Tokens are not security; **Enforcement** is security. All side-effects must pass through the Capability Gate.

### Capability Table
| Capability | Grant | Enforcement Point |
| :--- | :--- | :--- |
| `llm.call` | Permission to invoke external LLM providers | Cortex API Gateway |
| `net.egress` | Outbound network access outside the mesh | Soma HAL Proxy |
| `fs.write` | Persist data outside the instance root | Sandbox FS-Wrapper |
| `device.io` | Access to Local HW (TUI, Audio, BT) | Soma Unified Resource Mgr |

### Enforcement Rules
1. **Implicit Deny**: All capabilities are disabled unless explicitly granted in `config.toml`.
2. **Runtime Verification**: Every tool invocation must include a signed `CapabilityGrant`.
3. **Violation Policy**: Any attempt to bypass the gate triggers immediate **Organ Isolation** (Process Kill).

## 2. Organ Supervision & Lifecycle

IPPOC services are "organs" governed by a Supervisor contract.

### Startup Order
1. **Soma (The Body)**: Starts first. Acts as the Source of Truth for Identity, Trust, and Resource Allocation.
2. **Cortex (The Cognition)**: Starts only after Soma reports `/v1/health:OK`.
3. **Plugins/Tools**: Registered dynamically via Cortex.

### Supervision Law
- **Soma** restarts **Cortex** if cognition panics.
- **Heartbeat**: Every organ must report health to Soma every 30s.
- **Zombies**: Any process without a valid `NodeID` session is terminated.

## 3. Failure Playbook: The Law of Resilience

Behavior under stress must be deterministic.

| Stress Event | Deterministic Rule | Result |
| :--- | :--- | :--- |
| **Partial Connectivity** | Timeout (30s) -> Downgrade to Offline Fallback | System continues in "Degraded Mode" |
| **Infra Slowness** | Latency > 2x Baseline -> Load Shedding | Non-essential organs disabled |
| **Repeated Failure** | 3x consecutive crashes | Permanent Organ Isolation (Requires manual reset) |
| **Token Revoc** | Secret invalidation | Halt affected capability; Log Critical |

## 4. Sovereign Fallback Matrix

| Component | Target Infrastructure | Standalone Fallback |
| :--- | :--- | :--- |
| **Database** | PostgreSQL (pgvector) | SQLite (Localized) |
| **Messaging** | Redis Streams | Internal Asyncio Queue |
| **Trust** | Distributed Mesh | local-node Whitelist |

---
**Status**: Frozen Specification (v0.1.0)
*Code must obey the document, not the other way around.*
