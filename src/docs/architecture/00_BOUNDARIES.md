# IPPOC Architecture: Boundaries & Laws

> **STATUS**: CANON (Immutable)
> **VERSION**: 1.0

## 1. The Separation of Powers

The system is composed of two distinct entities that must never merge.

### **OpenClaw (Infrastructure / Body)**
- **Role**: Execution, Transport, Sensing, Actuation.
- **Nature**: Deterministic, Stateless (mostly), Rugged.
- **Responsibility**: "How to do it."
- **Components**:
    - Tool Execution
    - Plugins / Providers
    - HTTP / RPC / WebSocket
    - Cron / Scheduling
    - Retry Logic / Circuit Breakers
    - User Interface (TUI/Web)
- **Tag**: `@infra`

### **IPPOC (Cognition / Soul)**
- **Role**: Intent, Policy, Meaning, Evolution.
- **Nature**: Probabilistic, Stateful, Evolving.
- **Responsibility**: "What to do, and Why."
- **Components**:
    - Brain (Autonomy, Reasoning)
    - Memory (HiDB, Meaning extraction)
    - Economy (Budgeting, ROI)
    - Maintainer (Observer, Immune System)
- **Tag**: `@cognitive`

---

## 2. The Golden Rules of Interaction

1.  **Gravity flows Down**: Cognition commands Infrastructure. Infrastructure reports to Cognition.
    - *IPPOC* commands *OpenClaw* to execute tools.
    - *OpenClaw* sends signals (result, error) to *IPPOC*.

2.  **No Direct Organ Access**:
    - IPPOC Brain MUST NOT read OpenClaw's internal DB tables directly.
    - OpenClaw MUST NOT modify IPPOC's Neural Memory directly.
    - **Exception**: The `Observer` is allowed read-only access to specific OpenClaw signals for health monitoring.

3.  **The Orchestrator Gate**:
    - ALL actions (external API calls, expensive computations, file writes) MUST pass through the `ToolOrchestrator`.
    - No direct HTTP requests from the Brain.
    - No direct shell execution from the Brain.

---

## 3. Component Tags

All source files must carry one of these tags in their header to denote ownership.

- `@infra`: Owned by OpenClaw. Do not modify logic here for "AI reasons". Modify only for "bug/perf reasons".
- `@cognitive`: Owned by IPPOC. This is where the "thinking" happens.
- `@bridge`: Thin adapter code. Critical territory. Keep modification to a minimum.

---

## 4. Directory Map

| Path | Domain | Tag | Allowed Actions |
| :--- | :--- | :--- | :--- |
| `brain/core` | IPPOC | `@cognitive` | Reasoning, Planning |
| `brain/maintainer` | IPPOC | `@cognitive` | Observation, Evolution |
| `brain/memory` | IPPOC | `@cognitive` | Semantic Storage |
| `brain/cortex/openclaw` | OpenClaw | `@infra` | **DO NOT TOUCH LOGIC** |
| `body/mesh` | OpenClaw | `@infra` | Transport, Networking |
| `docs` | Shared | `@doc` | Documentation |

---
