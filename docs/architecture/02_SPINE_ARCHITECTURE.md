# 02_SPINE_ARCHITECTURE.md

## 1. The Spine (Tool Orchestrator)
The **Spine** is the central nervous system of an IPPOC Node. It allows the `Brain` (Cognition) to act upon the `Body` (Hardware/OS) and `Mind` (User Interface) safely, deterministically, and economically.

### 1.1 Core Principles
1.  **Single Entry Point**: All actions MUST flow through `orchestrator.invoke(envelope)`.
2.  **No Bypass**: Direct calls from Cognition to Body are forbidden.
3.  **Governance**: Every action is subject to Permission Checks, Budget Enforcement, and Audit Logging.

```mermaid
graph TD
    User[OpenClaw / User] -->|HTTP: /v1/tools/execute| Gateway[Universal Gateway]
    LangGraph[Cognitive Loop] -->|Python Call| Orchestrator
    
    Gateway --> Orchestrator
    
    subgraph "The Spine (Orchestrator)"
        Orchestrator --> Auth[Permission Check]
        Auth --> Budget[Budget Check]
        Budget --> LogPre[Audit Log (Start)]
        LogPre --> Router{Route Domain}
    end
    
    Router -->|domain=memory| MemAdapter[Memory Tool]
    Router -->|domain=body| BodyAdapter[Body Tool]
    Router -->|domain=evolution| EvoAdapter[Evolution Tool]
    Router -->|domain=cognition| ResAdapter[Research Tool]
    Router -->|domain=simulation| SimAdapter[WorldModel Tool]
    
    MemAdapter -->|gRPC/HTTP| HiDB
    BodyAdapter -->|Rust Bindings| RustKernel
```

## 2. The Protocol (ToolInvocationEnvelope)
Communication occurs exclusively via the **Envelope**:

```json
{
  "tool_name": "memory",
  "domain": "memory",
  "action": "store_episodic",
  "context": { "content": "I learned to fly today." },
  "risk_level": "low",
  "estimated_cost": 0.5
}
```

## 3. The Universal Gateway (Perfect Plugin)
External entities (like OpenClaw or other plugins) access the Spine via:
-   **Endpoint**: `POST /v1/tools/execute`
-   **Payload**: `ToolInvocationEnvelope`
-   **Response**: `ToolResult`

This allows any connected interface to utilize the full range of the organism's capabilities (Research, Self-Evolution, Simulation) without custom integration code.

## 4. Domain Governance
| Domain | Responsibility | Access | Risk Profile |
| :--- | :--- | :--- | :--- |
| **Memory** | Read/Write Knowledge | `memory.*` | Low |
| **Body** | Act on World (FS/Net) | `body.*` | High (Sandboxed) |
| **Evolution** | Mutate Self Code | `evolution.*` | Critical (Requires Rollback Token) |
| **Cognition** | Research/Learn | `research.*` | Medium (Costly) |
| **Simulation** | Test/Simulate | `simulation.*` | Medium (Compute Heavy) |

## 5. Security & Operations
### 5.1 Authentication
-   **Method**: Bearer Token (`Authorization: Bearer <IPPOC_API_KEY>`).
-   **Enforcement**: All mutation and tool endpoints (`/v1/tools/*`, `/v1/signals/*`) reject unauthorized requests (403).

### 5.2 Persistence
-   **Chat State**: Stored in `data/state/chat_rooms.json`. Survives restarts.
-   **Memory**: Stored in HiDB (Vector DB).

### 5.3 Identity
-   **Node ID**: Derived from cryptographic identity or `NODE_ID` env var.
-   **Hardening**: `bootstrap.py` ensures all internal organs are wired before external traffic is accepted.
