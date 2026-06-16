## 2024-05-22 - Async File I/O in Synchronous Methods
**Learning:** Even small JSON files (1000 items) can cause significant blocking (23ms) when written synchronously in a tight loop. `dataclasses.asdict` is relatively slow (5ms) but the main bottleneck was redundant disk writes. Offloading to `ThreadPoolExecutor` and removing redundant saves in `tick()` improved performance by 5x (23ms -> 4.7ms).
**Action:** When optimizing "save on every change" patterns, check if intermediate saves (like in `tick`) are necessary and offload the actual I/O to a background thread to unblock the main execution path.

## 2024-05-23 - Synchronous Audit Logging Bottleneck
**Learning:** `ToolOrchestrator._audit_action` was performing synchronous file I/O (open/write/close) for every tool invocation. This introduced ~68ms latency per 1000 calls. Moving this to a background thread with `queue.Queue` reduced it to ~3ms (20x improvement).
**Action:** For high-frequency logging or audit trails, always use an asynchronous writer or background thread to decouple I/O latency from the main execution path.

## 2025-03-03 - N+1 Query in Entity Similarity Search
**Learning:** Found an N+1 query issue in `find_similar_entities` where separate DB queries were made to fetch entity IDs and entity counts, unnecessarily increasing DB roundtrips.
**Action:** Replaced multiple sequential query calls with a single query using `LEFT JOIN` and `GROUP BY`, making it a single O(1) query fetch for candidate IDs and their metadata, reducing query latency and optimizing performance.

## 2025-03-03 - N+1 Query in Entity Similarity Search
**Learning:** Found an N+1 query issue in `find_similar_entities` where separate DB queries were made to fetch entity IDs, counts, and looping over individual records for relations, unnecessarily increasing DB roundtrips.
**Action:** Removed multiple sequential query calls and replaced loop-based traversal with a single unified Common Table Expression (CTE) query combining intersections and union calculations. It performs a single bulk fetch directly in SQL, scaling gracefully and dramatically reducing query latency by avoiding O(N) database roundtrips.
