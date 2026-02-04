# 11_MESH_TRUST_PROTOCOL.md

> **STATUS**: CANON (Cryptographic Trust)
> **PHASE**: 3 (Mesh Trust & behavioral Gating)

## 1. Goal
Move from "Verifiable Signals" to "Trustworthy Cognition" by hardening cryptography and introducing behavioral history (Reputation).

## 2. Real Ed25519 Signatures
- **Mechanism**: Every `SignedPacket` MUST use Ed25519 `Dalek` signatures.
- **Header**: Signature field contains the binary signature of `Hash(Payload || Timestamp || Nonce)`.
- **Validation**:
  - Valid Ed25519 signature.
  - Timestamp within drift limits (±300s).
  - Nonce unique (checked against local ReplayCache).

## 3. Admission State Machine (TrustLevel)
Nodes are categorized by their observed behavior over time. The state machine transitions are strictly governed by cryptographic verification and behavioral history.

| State | Trust Level | Capabilities |
| :--- | :--- | :--- |
| **UNKNOWN** | Zero | Connectivity only; insights logged but ignored. |
| **DISCOVERED**| Low | Node detected, handshake initiated. |
| **AUTHENTICATED**| Med | Handshake success; valid signatures confirmed. |
| **TRUSTED** | High | Reputation > 80; can influence mesh strategies. |
| **SYSTEM** | Absolute | Reserved for user-bootstrapped genesis nodes. |
| **BLACKLISTED**| -1 | Violations detected; all traffic dropped. |

### Transitions
- `UNKNOWN` → `DISCOVERED`: Peer detected via Discovery/Heartbeat.
- `DISCOVERED` → `AUTHENTICATED`: Successful cryptographic handshake.
- `AUTHENTICATED` → `TRUSTED`: Contributing `M` corroborated insights + Reputation threshold met.
- `*` → `BLACKLISTED`: Any signature failure or replay attack detected.

> [!IMPORTANT]
> **Refinement 1 (Security Surface Rule)**: Core security invariants (identity, admission, replay, trust) MUST NOT be disabled via feature flags.

### Handshake Placeholders (PROTOCOL SURFACE)
All handshake-related code not yet active MUST be labeled as:
`/// PROTOCOL SURFACE — NOT ACTIVE`
`/// Wired in Phase 4.5`

## 4. Persistent Reputation
- Reputation is bound to `NodeID`.
- Stored as a JSON object in the isolated node's `memory/reputation.db`.
- **Decay**: Reputation slowly decays during silence to protect against "hibernating and then poisoning".

## 5. Replay Protection
- `ReplayCache` maintains a Bloom filter or sliding window of seen Nonces.
- Duplicates are dropped immediately and trigger a reputation penalty.
