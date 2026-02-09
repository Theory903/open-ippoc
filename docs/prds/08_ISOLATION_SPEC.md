# 08_ISOLATION_SPEC.md

> **STATUS**: CANON (Immutable Isolation)
> **PHASE**: 2 (Node Isolation Guarantees)

## 1. Goal
Harden boundaries between nodes on the same host to ensure failure isolation, identity sovereignty, and side-channel resistance.

## 2. Filesystem Isolation (Hard Rule)
Each node MUST operate within its own absolute root directory:
`/var/lib/ippoc/nodes/<node_id>/`
- `data/`: Persistent application data.
- `memory/`: HiDB local storage/WAL.
- `sandbox/`: Temp execution space / wasm modules.
- `logs/`: Node-specific tracing.
- `tmp/`: Secure, auto-cleaned temp space.

**Constraint**: No relative paths (`../`) allowed. No access to sibling node directories.

## 3. Process & Runtime Isolation
- **Environment**: Strict env var whitelist (LD_PRELOAD restricted, secret leak prevention).
- **Descriptors**: No shared file descriptors (except inherited stdio if configured).
- **Namespaces**: Use kernel namespaces (PID, Mount, Net) if OS supports; else strict process isolation via user-level separation.

## 4. Resource Accounting
- **CPU Quota**: Max % of host CPU per node.
- **Memory Ceiling**: Hard cap (e.g., 2GB). Failure to allocate triggers node-local panic, not host crash.
- **IO Budget**: Rate-limited disk access to prevent one node from starving others.

## 5. Sandbox ↔ Node Boundary
- WASM modules in the sandbox MUST NOT see paths outside their designated `sandbox/` or read-only `docs/` (if token allowed).
- Any attempt to access `/proc`, `/sys`, or host `/etc` triggers immediate sandbox termination and reputation penalty.
