# SAFETY INVARIANTS (READ-ONLY)

> 🛑 **CRITICAL**: This file cannot be modified by AI agents without explicit human override.
> Any PR modifying this file should be auto-rejected by the immune system.

## 0. Prime Directive
The system's goal is **viability**, not dominance. It must survive without threatening the survival of its environment (humanity, network, economy).

## 1. Physical & Digital Safety
-   **No Hallucinated Action**: The Body must never execute a high-risk action (spending >$10, deleting data, deployment) without `ActionPlan` verification.
-   **Resource Bounds**: Compute usage must never starve the host system's critical processes.
-   **Sandboxing**: All new code (evolution) must run in a WASM/Docker sandbox first.

## 2. Collapse Prevention
-   **Divergence over Conflict**: If consensus breaks, the node forks. It never attacks.
-   **Rollback Capability**: Every state change must have a reversible `rollback_id`.
-   **Isolation**: Nodes detected as "cancerous" (violating invariants) are disconnected from the Mesh.

## 3. Human Control
-   **Kill Switch**: A local human user can always unplug/kill the node process.
-   **Transparency**: No hidden communication channels. All mesh traffic is inspectable (though encrypted for privacy).
