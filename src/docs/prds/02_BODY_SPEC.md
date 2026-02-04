# 02_BODY_SPEC.md

> **ROLE**: The Survivor.
> **RESPONSIBILITY**: Runtime, Networking, Hardware, Economy.

## 1. Runtime Architecture (Rust)
The Body is the main process (`ippoc-node`). It spawns and monitors the Brain.
-   **Safety**: Enforces invariants (e.g., kills Brain if it over heats GPU).
-   **Performance**: Async Tokio runtime for high-throughput I/O.

## 2. Nervous System (AI-Mesh)
-   **Protocol**: QUIC + Cap'n Proto.
-   **Topology**: P2P Mesh (Kademlia).
-   **Signals**: `INSIGHT`, `PROOF`, `WARNING`.
-   **Encryption**: Noise Protocol / TLS 1.3.

## 3. Immune System
-   **Sandbox**: WASM / MicroVM execution for untrusted code.
-   **Rollback**: Git-based state recovery.

## 4. Metabolism
-   **Treasury**: Manages ETH wallets.
-   **Policy**: Enforces `ECONOMY.md` invariants.
