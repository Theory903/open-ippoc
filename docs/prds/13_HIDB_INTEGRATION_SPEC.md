# 13_HIDB_INTEGRATION_SPEC.md

> **STATUS**: DRAFT (Planning Phase 5)
> **ROLE**: Memory Bridge (Mind <-> Memory)

## 1. Goal
Replace the default OpenClaw `memory-core` (simple file-backed) with the full IPPOC HiDB system (Postgres+Redis+Rust) to enable "Solid Hybrid RAG" and persistent cognitive state.

## 2. Architecture
The integration utilizes OpenClaw's Plugin API to inject HiDB as the primary memory provider.

```mermaid
graph TD
    User[User/Sub-Agent] -->|Query| OpenClaw[Mind: OpenClaw]
    
    subgraph "Extensions Layer"
        Native[extensions/hidb-native]
    end
    
    subgraph "IPPOC Core"
        RustBridge[Rust FFI / IPC]
        HiDB[HiDB Core (PgVector + Redis)]
    end
    
    OpenClaw -->|Plugin API| Native
    Native -->|gRPC/HTTP| RustBridge
    RustBridge -->|CognitivePacket| HiDB
```

## 3. The `hidb-native` Extension
A new OpenClaw extension located at `mind/openclaw/extensions/hidb-native`.

**Responsibilities:**
1.  **Intercept**: Hook into `memory_search` and `memory_get` tool calls.
2.  **Route**: Forward queries to the running HiDB Rust service.
3.  **Format**: Convert HiDB `CognitivePacket` responses into OpenClaw tool output format.
4.  **Directives**: Handle `/think` directives by querying HiDB's "reflexive" layer first.

## 4. Integration Logic
- **Read**: When `memory_search` is called, don't just grep files. Query HiDB's HNSW index.
- **Write**: When the agent "learns", send `ObservationPacket` to HiDB for ingestion.
- **Boot**: On OpenClaw startup, connect to IPPOC-O via `localhost:PORT`.

## 5. Transition Strategy
1.  **Phase A**: Create `hidb-native` extension skeleton.
2.  **Phase B**: Implement `LocalHiDBClient` in TypeScript to talk to IPPOC.
3.  **Phase C**: Register `memory_search` override in OpenClaw.
4.  **Phase D**: Disable `memory-core` and enable `hidb-native`.

## 6. Success Criteria
- [ ] OpenClaw `memory status` shows "HiDB Connected".
- [ ] `memory search "context"` returns results from Postgres/PgVector.
- [ ] Agent uses HiDB context in `/think` blocks.
