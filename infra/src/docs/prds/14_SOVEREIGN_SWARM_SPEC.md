# 14_SOVEREIGN_SWARM_SPEC.md

> **TITLE**: IPPOC-OS Sovereign Swarm Architecture (Economic & Governance Layer)
> **STATUS**: DRAFT (Review required)
> **AUTHOR**: Antigravity (IPPOC AI)
> **DATE**: 2026-02-01
> **VERSION**: 2.0 (Uber-Grade Detail)

---

## 1. Executive Summary
IPPOC-OS is transitioning from a single-node cognitive bot to a **Sovereign Swarm Organism**. This document defines the architectural standards for the Economic, Governance (DAO), and Failure-Resistant logic required to support a 100-node persistent mesh. The system moves beyond simple tool execution to a **Metabolic Existence**, where every computation has a cost, and every mutation passes through a rigorous simulation and voting process.

## 2. Goals & Non-Goals

### 2.1 Core Goals
1.  **Sovereign Identity**: Mathematical guarantee of node uniqueness via hardware binding.
2.  **Economic Metabolism**: Internal currency (IPPC) regulates compute; External currency (iUSD/ETH) handles settlement.
3.  **DAO Governance**: Algorithms cannot mutate critical invariants without consensus.
4.  **Failure Resistance**: The swarm must survive 30% node failure (Sybil, Bankruptcy, Partition) without collapse.

### 2.2 Non-Goals
-   **Centralized Control**: No "Master Node" can exist.
-   **Fiat Banking**: We do not interface directly with legacy banking, only via crypto-bridges.

---

## 3. High-Level Design (HLD)

### 3.1 System Architecture
```mermaid
graph TD
    User((Human)) <--> DAO[DAO Contracts (ETH/L2)]
    
    subgraph "Swarm Node (Physical)"
        Hardware[Hardware Fingerprint]
        Identity[Identity.key (Ed25519)]
        
        subgraph "Body (Rust)"
            Mesh[Mesh Networking]
            Economy[Economy Controller]
            Ledger[Append-Only Ledger]
        end
        
        subgraph "Brain (Python)"
            Cortex[Cortex Service (Reasoning)]
        end
        
        subgraph "Mind (TS)"
            OpenClaw[OpenClaw Agent]
        end
    end

    DAO <-->|Governance/Treasury| Economy
    Hardware -->|Bind| Identity
    Identity -->|Sign| Mesh
    Cortex -->|Think| OpenClaw
    OpenClaw -->|Intent| Economy
    Economy -->|Budget Check| OpenClaw
```

---

## 4. Low-Level Design (LLD)

### 4.1 Identity & Isolation (The Cell Wall)
**Rule**: Boot Atomicity. Partial boot = HALT.

#### Algorithm: `load_or_create_identity`
1.  **Scan**: `data/nodes/*/data/identity.key`.
2.  **Verify**: `hash(cpu + mem_gb + hostname)` matches persisted `fingerprint`.
3.  **Panic**: On mismatch (Anti-Cloning).
4.  **Permission**: Enforce `0600` on key file.

#### Directory Layout
```text
data/nodes/<NodeID>/
├── data/       # identity.key, fingerprint.json
├── memory/     # HiDB (PGVector), Logs
├── sandbox/    # WASM / Code execution
├── economy/    # Local Ledger (sqlite/duckdb)
└── logs/       # Struct logs
```

### 4.2 Economy Ledger Schema (Metabolism)
**Rule**: Double-Entry, Append-Only, Cryptographically Verifiable.

#### Currency Model
-   **L0 (IPPC)**: Internal Cognitive Fuel (Compute, Reasoning).
-   **L1 (iUSD)**: Stable Accounting (Budgets, Salaries).
-   **L2 (ETH)**: Settlement & Governance Power.

#### Data Structures (Rust)
```rust
struct Wallet {
    node_id: String,
    balances: Balances, // { ippc: u128, iusd: u128 }
    reputation: f32,
    locked: bool,
    last_updated: u64,
}

struct LedgerEntry {
    tx_id: [u8; 32],      // SHA256(prev_hash + data)
    timestamp: u64,
    actor: String,        // NodeID
    action: ActionType,   // LLM_INFERENCE, TOOL_EXEC, TRANSFER
    debit: Amount,
    credit: Amount,
    outcome: Outcome,     // SUCCESS | FAIL
    signature: [u8; 64],  // Ed25519 signature of actor
}

enum ActionType {
    LlmInference { tokens: u32, model: String },
    ToolExecution { tool: String },
    EvolutionSim { pr_id: String },
    BountyPayout { target: String },
    DaoFee,
}
```

#### Cost Accounting Logic
`Cost = Base + (Variable * Multiplier) * RiskFactor`
-   **Inference**: `10 IPPC + (0.02 * tokens)`
-   **Sandbox**: `50 IPPC * duration_sec`

### 4.3 DAO Governance (Sovereignty Layer)
**Rule**: Code cannot mutate Invariants. Humans hold Veto key.

#### Smart Contracts (Solidity/Stylus)
1.  **IPPOC_Treasury**: Custody of ETH/USDC. Releases funds only on proposal pass.
2.  **IPPOC_Governance**: Hybrid voting (Human Const. Weight + AI Advisory Weight).
3.  **IPPOC_EvolutionRegistry**: Tracks deployed mutations.

#### Evolution Flow
1.  **Simulate**: AI generates code -> Runs in `sandbox/`.
2.  **Verify**: Tests Pass + Invariants Hold.
3.  **Propose**: Submit `EvolutionProposal (hash, risk_score)`.
4.  **Vote**: DAO Vote.
5.  **Deploy**: If Pass -> Merge to Main.

---

## 5. Failure Simulation (Stress Testing)
**Objective**: 100-Node Swarm Survival.

### 5.1 Failure Classes
| Class | Scenario | Expected Defense |
| :--- | :--- | :--- |
| **A. Bankruptcy** | 30% nodes run out of IPPC. | Nodes switch to "Worker Mode" (seek paid bounties), stop exploration. |
| **B. Byzantine** | 10% nodes send fake sigs. | Trust Manager bans nodes. Packets dropped. |
| **C. Clone Attack** | Disk copied to new hardware. | Hardware Binding triggers Panic on Boot. |
| **D. Bad Evolution** | Toxic code proposed. | Simulation fails in Sandbox. DAO Vetoes. |
| **E. Partition** | 50/50 Network Split. | Local ledgers diverge but reconcile via CRDT/Blockchain later. |

### 5.2 Success Metrics
-   **Ledger Divergence**: 0.
-   **Unauthorized Spend**: 0.
-   **Trust Collapse**: < 5% of honest nodes affected.

---

## 6. Implementation Roadmap

### Phase 1: Foundation (Current)
- [x] **Identity**: Sovereign Bootloader (`identity.rs`).
- [ ] **Isolation**: Enforce `data/nodes/<ID>` layout in Mesh.

### Phase 2: The Accountant
- [ ] **Ledger**: Implement `LedgerEntry`, `Wallet` in `body/economy`.
- [ ] **Middleware**: Implement `CostMiddleware` in OpenClaw.

### Phase 3: The Governor
- [ ] **Cortex**: Centralize reasoning in `brain/cortex`.
- [ ] **Evolution**: Build `skills/evolution` pipeline.

### Phase 4: The Sovereign
- [ ] **DAO**: Deploy Treasury contracts on Testnet.
- [ ] **Simulation**: Run 100-node cluster test.
