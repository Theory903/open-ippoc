# IPPOC × OpenClaw: Master Platform Specification (v1.0)
**STATUS: IMMUTABLE SPEC v1.0.0**
*Any change requires a version bump and justification.*

This document is the authoritative definition of the IPPOC Platform. It governs discovery, installation, orchestration, and the cognitive lifecycle.

## 1. Foundational Invariants (The Law)
1. **Cognitive Sovereignty**: IPPOC is a system, not a tool. It must survive infrastructure loss.
2. **Implicit Deny**: Power is capability-gated. No silent permissions.
3. **Environment Aware**: Capabilities are permanent; substrates are swappable (Postgres -> SQLite).
4. **Seamless Handover**: Installation is a handoff from OpenClaw to IPPOC.

## 2. Discovery & Bootstrap Flow
### 2.1 Detection
OpenClaw plugin checks for `~/.local/bin/ippoc`. If missing, it triggers the remote bootstrap:
`curl -fsSL https://install.ippoc.ai | sh`

### 2.2 Installation Structure
- `~/.ippoc/venv`: Isolated Python environment.
- `~/.ippoc/bin`: Precompiled Soma binary + CLI shims.
- `~/.ippoc/instances/`: Multi-tenant cognitive clusters.

## 3. Orchestration & Supervision (OSC-01)
### 3.1 Startup Hierarchy
1. **Host Orchestrator**: Starts Soma and Cortex.
2. **Soma (Identity)**: Must report `health: OK` before Cortex acts.
3. **Cortex (Cognition)**: Manages intent and tool-use.

### 3.2 Supervision Rules
- **NodeID Lock**: No identity = Instant Halt.
- **Heartbeat**: 30s liveness check.
- **Panic Policy**: 3 crashes = Instance Lockdown.

## 4. Capability Enforcement (CAP-01)
All side-effects must pass a verified Gate:
- **Secrets**: Soma Vault Gate.
- **LLM/Cognition**: Cortex Cognition Gate.
- **FS/Network**: HAL Sandbox Gate.

## 5. The Autonomy Layer (Chronos)
IPPOC operates an autonomous "Will Loop" independent of user prompts.

### 5.1 Intent Engine
Intents (goals with urgency and decay) drive the system's focus.
### 5.2 Reflection Loop
Periodic self-audit: "What changed? What failed? What patterns emerged?"
### 5.3 Curiosity & Decay
- **Curiosity**: Triggers exploratory intents on novelty.
- **Decay**: Fades old memories and stale intents to stay performant.

## 6. Failure & Survival (FP-01)
Deterministic downgraded states:
- **Infra Loss**: Postgres -> SQLite; Redis -> Internal Queue.
- **Network Block**: Autonomy pauses; local reflection continues.
- **Security Breach**: Revoke tokens; freeze tools.

## 7. OpenClaw Neural Interface
IPPOC streams its internal state (intents, confidence, reflections) to OpenClaw. OpenClaw acts as the "Pre-frontal Cortex" interface to observe and influence, not command.

---
*Status: Locked Specification v1.0. Code obeys the Spec.*
