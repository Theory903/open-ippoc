# 07_HARDENING_SPEC.md

> **STATUS**: CANON (Immutable Hardening)
> **RETROSPECTIVE**: Closure of systemic loops identified in adversarial audit.

## 0. Meta-Rule (Absolute)
Every autonomous capability must have an explicit failure mode, ceiling, and stop condition. If any are missing, the capability is disabled by default.

## 1. Mesh Cognition Hardening
- **Insight Admission**: Signed packets, Reputation-weighted confidence, Cross-node corroboration (N ≥ 3), Local counterfactual test in WorldModel.
- **Byzantine Resistance**: Median-of-means aggregation for gradients/strategies.

## 2. Role Drift Elimination
- **Capability Tokens**: Kernel/Runtime enforced tokens (THINK, PLAN, EXECUTE_SANDBOX, etc.).
- **Mutation Gate**: Role changes require hardware proof + Human/DAO approval + cool-down.

## 3. Memory Truth Protection
- **Outcome-Weighted Confidence**: Confidence += success / -= failure. Retrieval != validation.
- **Source Trust Classes**: Immutable tags (HUMAN_VERIFIED, TOOL_OUTPUT, MESH_DERIVED, etc.).

## 4. Self-Evolution Goal Bounding
- **Fitness Function Lock**: F = Stability + Correctness + Energy Efficiency. Forbidden: Revenue maximization at cost of safety.
- **Cross-Patch Interaction**: Test patch with last K merges.

## 5. ToolSmith Defense
- **Capability Declaration**: Mandatory `ToolManifest` with syscall allowlist.
- **Dependency Quarantine**: Vendored, hash-pinned, no runtime downloads.

## 6. Simulation Fidelity
- **Reality Parity Index (RPI)**: |simulated_metrics - real_metrics|. Threshold guard.

## 7. Kernel Actuation Control
- **Formal Bounds**: Δaction ≤ ε per unit time (Rate-limited GUARANTEE).
- **Control Theory**: PID damping, no direct feedback loops.

## 8. Emergency Control
- **Local Hard Kill**: Physical kill, Kernel panic trigger, Network isolation.
- **Mesh Freeze**: Systemic anomaly triggers read-only mode.

## 9. Utility Ceiling
- **MAX_OBJECTIVE**: `system_viability`.
- **Meaning Source**: Only humans define purpose/value.
