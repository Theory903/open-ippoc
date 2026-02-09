# IPPOC Supervision Rules (SR-01)
**STATUS: IMMUTABLE LAW v1.0.0**
*Any change requires a version bump and justification.*

## 1. The Organ Supervisor

IPPOC uses a **Tree-Based Supervision** model.

1. **Host (PID 1 equivalent)**: The OS process running the `ippoc` CLI.
2. **Body (Soma)**: The root organ. Started directly by the Host.
3. **Brain (Cortex)**: The secondary organ. Started by the Host but verified by Soma.
4. **Skills/Plugins**: Tertiary processes. Spawned by Cortex, audited by Soma.

## 2. Startup & Dependency Chain

- **Sovereign Order**: `Soma` -> `Cortex` -> `Plugins`.
- **Health Dependency**: Cortex may NOT begin tool-use or autonomy loops until Soma returns `v1/health: OK`.
- **Identity Lock**: If Soma fails to retrieve the `NodeID` from the Vault within 10s, the entire instance must HALT.

## 3. Supervision Enforcement

### Who Starts Whom?
- The **CLI Orchestrator** starts both `Soma` and `Cortex` as sibling processes.
- The **Orchestrator** is responsible for initial resource allocation (ports, memory limits).

### Who Restarts Whom?
- The **CLI Orchestrator** monitors both processes.
- If `Cortex` fails: Orchestrator restarts it up to 3 times.
- If `Soma` fails: Orchestrator MUST kill `Cortex` and restart the entire cluster. Soma is the identity source; without it, Cortex is a ghost.

### Who Kills Whom?
- **Host** kills **All** on `SIGINT` or `SIGTERM`.
- **Soma** kills **Cortex** if it detects a Capability Violation.
- **Cortex** kills **Plugins** if they exceed their budget or time-slice.

## 4. Failure Thresholds

- **Liveness Timeout**: 30s. No heartbeat in 30s = Terminated.
- **Panic Rate**: 3 crashes in 5 minutes = Instance Lockdown (Manual intervention required).
- **Silent Failure**: If an organ is alive but returning `5xx` for 60s, it is treated as a zombie and killed.
