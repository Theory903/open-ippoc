# IPPOC Failure Playbook (FP-01)
**STATUS: IMMUTABLE LAW v1.0.0**
*Any change requires a version bump and justification.*

## 1. Downgrade Strategy
Tines the deterministic survival procedures for IPPOC organs during catastrophic infrastructure failure.

## 1. Database Unreachable (Postgres)
- **Constraint**: Do NOT stall main loop.
- **Action**: Wait 5s. On timeout, HOT-SWAP to local SQLite instance.
- **Notification**: Log `[HiDB] WARNING: Postgres lost. Entering Degraded Persistence Mode.`
- **Recovery**: Polling every 60s. Auto-sync if Postgres returns.

## 2. Shared Memory Unreachable (Redis)
- **Constraint**: Zero loss of high-priority internal events.
- **Action**: Instantly divert all traffic to internal `asyncio.Queue`.
- **Side-Effect**: Multi-node telepathy is halted. System becomes "Instance-Local".
- **Notification**: Log `[Cortex] WARNING: Redis lost. Isolation Mode active.`

## 3. Token Revocation / Secret Invalidated
- **Constraint**: Safety > Liveness.
- **Action**: Immediately HALT all tools requiring that scope. Do NOT attempt re-auth with cached keys.
- **State**: The organ enters "Provisional State".
- **Notification**: Log `[Soma] CRITICAL: Capability Token Revoked. Access Terminated.`

## 4. Sandbox Crash (HAL)
- **Constraint**: Host integrity is the prime directive.
- **Action**: Kill the parent wrapper. Do NOT attempt immediate restart of the specific tool.
- **Rule**: If a tool crashes 3 times, it is BLACKLISTED until a manual `ippoc reset <name>` is issued.

## 5. Network Egress Blocked
- **Constraint**: Autonomy must pause.
- **Action**: Block all autonomy loops that depend on external perception.
- **Internal Loop**: Continue with local pattern recognition and pattern storage.
- **Notification**: Log `[HAL] WARNING: Egress Blocked. Autonomy Paused.`
