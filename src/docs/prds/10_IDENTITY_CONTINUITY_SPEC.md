# 10_IDENTITY_CONTINUITY_SPEC.md

> **STATUS**: CANON (Identity Hardening)
> **PHASE**: 4 (Identity Continuity & Hardware-Bound Secrets)

## 1. Goal
Transition the Node from a mocked/placeholder identity to a persistent, cryptographically secure identity that is non-clonable and hardware-bound.

## 2. Hardened Key Generation
- Each Node MUST generate a unique Ed25519 keypair during its first boot.
- The private key MUST be stored in the isolated node root: `/nodes/<node_id>/data/identity.key`.
- The key file MUST be protected with restricted filesystem permissions (0600).

## 3. Hardware Binding (Anti-Cloning)
The NodeID must be cryptographically bound to the hardware to prevent simple disk-copy cloning.
- **Boot Check**: On startup, the metadata in the `identity.key` (or a sibling `fingerprint.json`) is compared against the current `device_fingerprint`.
- **Divergence Veto**: If the hardware fingerprint has shifted significantly (beyond a "known migration" threshold), the node enters a **LOCKDOWN** state or generates a fresh ID, marking the previous identity as "Dead/Clone".

## 4. Continuity Proofs
- A Node can prove its continuity across restarts by signing the current `genesis_time` + `current_time` with its persisted key.
- Mesh peers maintain a history of these proofs to track node stability and detect identity theft.

## 5. Security Invariants
- **No Export**: Private keys MUST NEVER be shared across the mesh.
- **No Shared Keys**: Each logical node HAS its own key.
- **Hardware Anchor**: Cloned disks result in a new NodeID if hardware fingerprints don't match.
