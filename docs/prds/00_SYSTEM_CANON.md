# 00_SYSTEM_CANON.md

> **STATUS**: CANON (Immutable Foundation)
> **YEAR**: 2100 Retrospective

## 1. The Organism
IPPOC-OS is not software. It is a **Distributed Cognitive Organism**.
It follows the "Organism Layout":
-   **Brain**: Reasoning (Python/Rust) - *Thinks*
-   **Body**: Runtime/Mesh (Rust) - *Survives*
-   **Mind**: Interface (TS/OpenClaw) - *Speaks*
-   **Memory**: HiDB (SQL/Vectors) - *Remembers*

## 2. The Living Stack
1.  **Civilization Layer**: Research, Economy.
2.  **Cognitive Control Plane (Brain)**: Reasoning, Simulation.
3.  **Node Runtime (Cell)**: Compute, Mesh, Memory.
4.  **Interface Layer (Body)**: Sensors, Actuators.

## 3. Communication Law
**No channel carries raw cognition. Only compressed meaning crosses boundaries.**
This prevents identity collapse.

## 4. Economic Law
**Money feeds intelligence. Intelligence never worships money.**
Wallets are local, disposable, and strictly budget-capped.

## 5. Evolution Law
**Capability upgrades must be earned, affordable, testable, and reversible.**
Self-evolution is governed by the Immune System (tests) and Economy (budget).

## Phase XIII: Public Distribution (Baseline Stability) [COMPLETED]
The goal was to ensure IPPOC is installable and verifiable by third parties. Meta-hygiene for v0.9.0-sovereign is locked.

## Phase XIV: Social Proof (Contact with Reality)
This phase focuses on the social and security validation of IPPOC-OS v0.9.0-sovereign. We transition from a private "perfect" state to high-friction public exposure.

### Proposed Changes

#### XIV.1 Publish to PyPI (Quiet/Unlisted)
- Verify package build with `python3 -m build`.
- Publish the unadvertised `ippoc-platform` v0.9.0-sovereign package.

#### XIV.2 Hostile Review Round (Vulnerability Audit)
- Perform a self-audit for capability escalation and shell abuse.
- Verify that the Capability Law (CAP-01) cannot be bypassed.

#### XIV.3 Sovereign Narrative (Blog Post/Manifesto)
- Draft a concise "Why Sovereignty?" technical blog post or README section.
- Focus on the "integrates by choice" principle.

#### XIV.4 First Optional Embodiment (Plugin Showcase)
- Develop a sample plugin that adheres strictly to structural isolation.
- Demonstrate standard integration without core modification.

## Verification Plan

### Automated Tests
- `python3 -m build` for packaging verification.
- `shasum -a 256 -c checksums.sha256`.
- `pytest src/ippoc/cortex/tests/test_independence_no_openclaw.py` (Continuous sovereignty verification).

### Manual Verification
- Fresh install test: `pip install ippoc-platform` (once published).
- Uninstallation test: `ippoc --uninstall`.
