# 09_MESH_HARDENING_SPEC.md

> **STATUS**: CANON (Communication Hardening)
> **PHASE**: 3 (Node ↔ Mesh Protocol Hardening)

## 1. Goal
Harden the neural mesh to prevent insight poisoning, gradient/strategy corruption, and unauthorized node discovery.

## 2. Signed Insight Packets (SIP)
Every message shared across the mesh MUST be signed by the originating Node's private key.
- **Packet Structure**: `Header { NodeID, Signature, Timestamp, Nonce } | Payload`.
- **Validation**: Incoming packets are rejected if signature is invalid or timestamp/nonce suggests replay attack.

## 3. Insight Admission Protocol (IAP)
Admission is not trust. Insights must pass the following pipeline before reaching HiDB:
1. **Reputation Filter**: Reject or flag if Sender's reputation < Threshold.
2. **Coherence Check**: Verify insight doesn't contradict established local Semantic Memory.
3. **Corroboration (N ≥ 3)**: High-impact strategies require corroboration from multiple distinct NodeIDs from different hardware if possible.

## 4. Byzantine-Resistant Aggregation
When multi-node reasoning or training is used:
- Use **Median-of-Means** aggregation for gradients.
- Detect and prune "outlier" nodes that consistently provide divergent or hostile signals.

## 5. Discovery & Admission Control
- **Probation Window**: New nodes are observed in "read-only" or "low-trust" mode for a configurable period/epoch.
- **Mutual Authentication**: Nodes MUST mutually authenticate before exchanging non-public abstractions.
