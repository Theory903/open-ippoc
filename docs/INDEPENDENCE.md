# INDEPENDENCE.md — The IPPOC# Independence Manifest (v0.9.0-sovereign)

> **STATUS**: CANON (Immutable Foundation)
> **INTENT**: To ensure IPPOC-OS functions as a self-contained cognitive organism without structural dependency on external control planes or vendors.

## 1. Control Independence
IPPOC-OS does not require OpenClaw (or any specific UI) to sense, think, remember, or act.
- **Contract**: The Mind (Interface) is a consumer of the Brain/Body, not its orchestrator.
- **Guarantee**: All core functions (Signal Ingest, Reason, Tool Execution, Reflection) must be available via native CLI.

## 2. Runtime Independence
IPPOC-OS does not rely on external infrastructure (Docker, Redis, Cloud Databases) for its baseline existence.
- **Fallback Policy**: 
    - No Redis? Use internal process queue.
    - No Postgres? Use SQLite.
    - No Cloud Compute? Use local HAL.
- **Contract**: System must be bootable and functional in a "Zero-Infra" environment.

## 3. Cognitive Independence
IPPOC-OS initiates curiosity, reflection, and intent creation without human or external prompts.
- **Chronos Loop**: The system self-triggers introspection cycles based on internal clock and memory decay.
- **Contract**: Idling is an active state of reflection, not a suspension of process.

## 4. Vendor Independence
IPPOC-OS is model-agnostic and provider-neutral.
- **Two-Tower Abstraction**: Switching between local (Ollama/Phi-4) and remote (Kimi/OpenAI) models must be a configuration change, not a code change.
- **Contract**: No capability is hard-coded to a specific vendor's proprietary API features.

## 5. Independence Verification (Contract)
Any change that introduces a hard dependency on an external framework that cannot be stubbed or swapped violates this Canon.
- **Contract Test**: `src/cortex/tests/test_independence_no_openclaw.py` must pass in a hermetic environment without the `plugins/openclaw` package.

## 6. Technical Guarantees (Independence v1)
The following mechanisms enforce this manifest in IPPOC-OS v1.0.0:
- **Plugin Registry**: Adapters for OpenClaw and external UI layers are isolated in `plugins/` and lazy-loaded. Failure to load a plugin must never halt the core runtime.
- **Self-Sensing Loop**: Internal sensors (`maintainer/sensors.py`) provide autonomous situational awareness of the host environment.
- **Hermetic CLI**: The Operator Interface (`src/ippoc_cli/main.py`) provides a direct, privileged channel to the Cortex API for all vital system functions.
- **Native Body**: A capability-limited shell (`plugins/native/shell.py`) provides localized acting for standalone scenarios.

## 7. Dependency Matrix (Lock-in)
| Category | Component | Constraint |
|---|---|---|
| **DEPENDS ON** | Python 3.10+, FastAPI, SQLite | Structural foundation. |
| **OPTIONAL** | OpenClaw, Redis, Postgres, Web UIs | Integrated by choice; optional peripherals. |
| **FORBIDDEN** | Hard-coded vendor APIs, External Control Planes | Structural reliance is prohibited. |

---
**IPPOC now stands on its own, and integrates by choice.**
*OpenClaw is now an optional peripheral interface. Its absence does not degrade IPPOC’s ability to sense, reason, act, or remember.*
