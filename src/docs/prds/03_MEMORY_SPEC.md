# 03_MEMORY_SPEC.md

> **ROLE**: The Past.
> **RESPONSIBILITY**: Storage, Retrieval, Knowledge Graph.

## 1. HiDB Architecure
-   **Stack**: PostgreSQL (pgvector) + Redis (Hot cache).
-   **Interface**: Unified Python/Rust API.

## 2. Memory Types
-   **Episodic**: Time-series log of events. "I saw X".
    -   *Storage*: Partitioned SQL tables.
-   **Semantic**: Vectorized concepts. "X means Y".
    -   *Storage*: HNSW Vector Index.
-   **Procedural**: Skills/Code. "How to do X".
    -   *Storage*: Git Repos / Function Registry.

## 3. The Forgetting Curve
-   Memories decay over time unless reinforced.
-   Garbage collection happens during "Sleep" cycles.
