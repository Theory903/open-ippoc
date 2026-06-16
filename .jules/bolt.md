## 2024-05-22 - Async File I/O in Synchronous Methods
**Learning:** Even small JSON files (1000 items) can cause significant blocking (23ms) when written synchronously in a tight loop. `dataclasses.asdict` is relatively slow (5ms) but the main bottleneck was redundant disk writes. Offloading to `ThreadPoolExecutor` and removing redundant saves in `tick()` improved performance by 5x (23ms -> 4.7ms).
**Action:** When optimizing "save on every change" patterns, check if intermediate saves (like in `tick`) are necessary and offload the actual I/O to a background thread to unblock the main execution path.

## 2024-05-23 - Synchronous Audit Logging Bottleneck
**Learning:** `ToolOrchestrator._audit_action` was performing synchronous file I/O (open/write/close) for every tool invocation. This introduced ~68ms latency per 1000 calls. Moving this to a background thread with `queue.Queue` reduced it to ~3ms (20x improvement).
**Action:** For high-frequency logging or audit trails, always use an asynchronous writer or background thread to decouple I/O latency from the main execution path.

## 2024-05-24 - [N+1 query optimization using SQL CTEs]
**Learning:** Calculating Jaccard similarity across large graph relations with nested database queries resulted in an N+1 query issue, causing significant performance bottlenecks (e.g. 14.1s overhead).
**Action:** Re-write the nested relation intersections using SQL Common Table Expressions (CTEs) directly in the database logic to achieve intersection-first operations in a single database roundtrip, effectively removing N+1 overhead and boosting performance to ~0.0345s for the same dataset size.
