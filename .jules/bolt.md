## 2024-05-22 - Async File I/O in Synchronous Methods
**Learning:** Even small JSON files (1000 items) can cause significant blocking (23ms) when written synchronously in a tight loop. `dataclasses.asdict` is relatively slow (5ms) but the main bottleneck was redundant disk writes. Offloading to `ThreadPoolExecutor` and removing redundant saves in `tick()` improved performance by 5x (23ms -> 4.7ms).
**Action:** When optimizing "save on every change" patterns, check if intermediate saves (like in `tick`) are necessary and offload the actual I/O to a background thread to unblock the main execution path.

## 2024-05-23 - Synchronous Audit Logging Bottleneck
**Learning:** `ToolOrchestrator._audit_action` was performing synchronous file I/O (open/write/close) for every tool invocation. This introduced ~68ms latency per 1000 calls. Moving this to a background thread with `queue.Queue` reduced it to ~3ms (20x improvement).
**Action:** For high-frequency logging or audit trails, always use an asynchronous writer or background thread to decouple I/O latency from the main execution path.

## 2026-05-23 - [Graph Entity Similarity Optimization]
**Learning:** N+1 queries in similarity searches (fetching full entity relationships in a loop) cause exponential slowdowns as the knowledge graph grows, hitting ~8.7s for 10,000 unrelated entities.
**Action:** When calculating similarity metrics like Jaccard index in databases, push the computation down to SQL using Common Table Expressions (CTEs) and JOINs to filter candidates based on intersections first. This avoids full table scans and reduces execution time drastically (measured ~0.008s, >1000x improvement).
