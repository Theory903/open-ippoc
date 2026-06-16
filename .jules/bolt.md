## 2024-05-22 - Async File I/O in Synchronous Methods
**Learning:** Even small JSON files (1000 items) can cause significant blocking (23ms) when written synchronously in a tight loop. `dataclasses.asdict` is relatively slow (5ms) but the main bottleneck was redundant disk writes. Offloading to `ThreadPoolExecutor` and removing redundant saves in `tick()` improved performance by 5x (23ms -> 4.7ms).
**Action:** When optimizing "save on every change" patterns, check if intermediate saves (like in `tick`) are necessary and offload the actual I/O to a background thread to unblock the main execution path.

## 2024-05-23 - Synchronous Audit Logging Bottleneck
**Learning:** `ToolOrchestrator._audit_action` was performing synchronous file I/O (open/write/close) for every tool invocation. This introduced ~68ms latency per 1000 calls. Moving this to a background thread with `queue.Queue` reduced it to ~3ms (20x improvement).
**Action:** For high-frequency logging or audit trails, always use an asynchronous writer or background thread to decouple I/O latency from the main execution path.
## 2024-05-27 - Entity Similarity SQL Query Optimization
**Learning:** Found an opportunity to collapse multiple preliminary database queries (fetching a reference entity's ID and relation count) into a single optimized Jaccard similarity CTE query. By pushing scalar queries directly into the CTE (`WITH ref_entity AS (...)`), we removed two extra network round-trips to the database while maintaining exact functional behavior.
**Action:** Always inspect iterative or multi-step database interactions for opportunities to merge them into a single comprehensive SQL query, particularly utilizing CTEs for intermediate values and aggregates, reducing overall database connection overhead and latency.
