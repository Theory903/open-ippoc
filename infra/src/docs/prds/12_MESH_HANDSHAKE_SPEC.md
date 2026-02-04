# 12_MESH_HANDSHAKE_SPEC.md

> **STATUS**: CANON (Trust Initiation)
> **PHASE**: 3 (Mesh Trust & Handshake Protocol)

## 1. Goal
Establish a secure, authenticated bridge between two sovereign nodes and initialize their mutual TrustLevel.

## 2. Handshake Sequence

The handshake is a 3-way exchange used to verify identity and public keys.

### 1. SYN (Initiation)
- **Sender**: Node A
- **Payload**: `{"type": "HS_SYN", "node_id": "A", "timestamp": T1, "nonce": N1}`
- **Signature**: Signed by A's private key.

### 2. SYN-ACK (Challenge/Response)
- **Receiver**: Node B
- **Payload**: `{"type": "HS_SYN_ACK", "node_id": "B", "challenge_nonce": N1, "timestamp": T2, "nonce": N2, "verifying_key": "B_PUB_KEY"}`
- **Signature**: Signed by B's private key.
- **Verification**: Node A verifies B's public key matches B's NodeID and signature is valid.

### 3. ACK (Finalization)
- **Sender**: Node A
- **Payload**: `{"type": "HS_ACK", "node_id": "A", "challenge_nonce": N2, "verifying_key": "A_PUB_KEY"}`
- **Signature**: Signed by A's private key.
- **Verification**: Node B verifies A's public key matches A's NodeID and signature is valid.

| Interval | Event | Action |
| :--- | :--- | :--- |
| **T=0** | Handshake Success | State = `AUTHENTICATED`. Public key pinned. |
| **T=1 Epoch**| Baseline Valid | State = `AUTHENTICATED`, Score improves. |
| **T=M Days** | Reputation Threshold | State = `TRUSTED` if Score >= 80. |

## 4. Key Pinning
Once a handshake is completed, the public key for `NodeID X` is **PINNED** in Node A's local `memory/peers.json`. Subsequent packets from `X` with a different key are rejected as **IDENTITY THEFT**.

## 5. Timing and Failure Modes

| Metric | Threshold | Action |
| :--- | :--- | :--- |
| **Handshake Timeout** | 10s | Drop connection, clear session. |
| **Max Retries** | 3 | Block IP temporarily (60s). |
| **Clock Skew** | ±300s | Termination. |
| **Invalid Signature**| Immediate | Move NodeID to `REJECTED` state. |

## 6. Trust State Machine Transitions

1. **UNKNOWN** (Start)
2. **DISCOVERED**: Node detected via Hearbeat.
3. **AUTHENTICATED**: Handshake completed successfully.
4. **TRUSTED**: Reputation threshold met (Score >= 80).
5. **BLACKLISTED**: Any signature mismatch or replay attempt.
6. **SYSTEM**: User-bootstrapped genesis.

---
## 7. Handshake Material Invariant
All Handshake messages MUST be wrapped in a `SignedPacket` envelope. Handshake initiation uses a temporary "boot" signature if the peer is truly unknown, but NodeIDs MUST match the public keys provided in the `HS_SYN_ACK`.
