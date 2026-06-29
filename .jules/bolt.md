## 2024-05-22 - Async File I/O in Synchronous Methods
**Learning:** Even small JSON files (1000 items) can cause significant blocking (23ms) when written synchronously in a tight loop. `dataclasses.asdict` is relatively slow (5ms) but the main bottleneck was redundant disk writes. Offloading to `ThreadPoolExecutor` and removing redundant saves in `tick()` improved performance by 5x (23ms -> 4.7ms).
**Action:** When optimizing "save on every change" patterns, check if intermediate saves (like in `tick`) are necessary and offload the actual I/O to a background thread to unblock the main execution path.

## 2024-05-23 - Synchronous Audit Logging Bottleneck
**Learning:** `ToolOrchestrator._audit_action` was performing synchronous file I/O (open/write/close) for every tool invocation. This introduced ~68ms latency per 1000 calls. Moving this to a background thread with `queue.Queue` reduced it to ~3ms (20x improvement).
**Action:** For high-frequency logging or audit trails, always use an asynchronous writer or background thread to decouple I/O latency from the main execution path.
## 2024-05-14 - Optimized Entity Similarity Search
**Learning:** Performing N+1 queries in high-volume paths (like entity similarity matching across the entire knowledge graph) causes extreme database bottlenecking due to round-trip latency. Iterating through all entities to calculate Jaccard similarity manually in Python compounds this issue significantly as graphs scale.
**Action:** When calculating relational overlap or subsetting entities in database-backed graphs, offload the computation (e.g., Jaccard similarity) directly into a CTE-based SQL query. Group candidate interactions and aggregate statistics natively in SQL rather than iterating in application logic to avoid full table scans and multiple query trips.
