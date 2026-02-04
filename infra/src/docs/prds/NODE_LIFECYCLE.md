# IPPOC-OS — Node Lifecycle Specification

**Status:** Canonical
**Version:** 1.0

## 0. Core Principle
A node is a **sovereign economic and cognitive actor**.
Lifecycle = **birth → contribution → trust → evolution → death**

---

## 1. Node Birth

### 1.1 Birth Triggers
1.  **Genesis Birth**: Initial swarm bootstrap.
2.  **DAO-Approved Spawn**: DAO grants funds + identity slot.
3.  **Economic Reproduction**: Node earns enough to spawn a child.
4.  **Human-Anchored Birth**: Human provisions hardware.

### 1.2 Birth Ceremony (Atomic)
1.  Generate Ed25519 keypair.
2.  Derive NodeID = `SHA256(pubkey)`.
3.  Create isolation root (`data/nodes/<NodeID>/`).
4.  Persist `identity.key` (0600).
5.  Bind hardware fingerprint.
6.  Initialize wallet (zeroed).
7.  Register in mesh as `Newborn`.

---

## 2. Early Life (Newborn → Active)
Newborns are restricted to prevent Sybil attacks.

| Capability | Allowed |
| :--- | :--- |
| Read Memory | ❌ |
| Propose Evolution | ❌ |
| Spend ETH | ❌ |
| Earn IPPC | ✅ |

**Promotion Criteria**:
- Identity verified by ≥ 3 trusted peers.
- No protocol violations.
- Minimum IPPC balance achieved.

---

## 3. Adulthood (Active → Trusted)

### 3.1 Active Node
- Full cognition and tool usage.
- Can earn IUSD.
- CANNOT spawn or vote yet.

### 3.2 Trusted Node
- **Criteria**: Long-term stability, positive economic contribution.
- **Powers**: Vote in DAO, Propose Evolution, Spawn Children.

---

## 4. Reproduction
- **Cost**: Requires significant IUSD/ETH.
- **Inheritance**: Child gets economic seed but **NO** keys/memory from parent.

---

## 5. Aging & Dormancy
- **Decay**: IPPC decays (entropy).
- **Dormancy**: If IPPC < min or inactive for T days.
- **Effect**: Dormant nodes cannot reason or evolve.

---

## 6. Death
1.  **Graceful Shutdown**: Retirement (flush memory, archive identity).
2.  **Economic Death**: Insolvency (wallet locked).
3.  **Slashing**: Punitive death for violations (assets seized).
4.  **Sudden Death**: Hardware loss (heartbeat failure).

---

## 7. Afterlife
Dead nodes are archived for forensics and governance memory.
