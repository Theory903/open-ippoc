## 2024-05-22 - Async File I/O in Synchronous Methods
**Learning:** Even small JSON files (1000 items) can cause significant blocking (23ms) when written synchronously in a tight loop. `dataclasses.asdict` is relatively slow (5ms) but the main bottleneck was redundant disk writes. Offloading to `ThreadPoolExecutor` and removing redundant saves in `tick()` improved performance by 5x (23ms -> 4.7ms).
**Action:** When optimizing "save on every change" patterns, check if intermediate saves (like in `tick`) are necessary and offload the actual I/O to a background thread to unblock the main execution path.

## 2024-05-23 - Synchronous Audit Logging Bottleneck
**Learning:** `ToolOrchestrator._audit_action` was performing synchronous file I/O (open/write/close) for every tool invocation. This introduced ~68ms latency per 1000 calls. Moving this to a background thread with `queue.Queue` reduced it to ~3ms (20x improvement).
**Action:** For high-frequency logging or audit trails, always use an asynchronous writer or background thread to decouple I/O latency from the main execution path.
## 2026-04-23 - Avoid N+1 Queries in Graph Traversals
**Learning:** Python-level BFS loops over database relations can result in severe N+1 query bottlenecks on dense graphs.
**Action:** Replace iterative edge lookups with Recursive CTEs (`WITH RECURSIVE`), pushing path finding down to the database engine. Ensure SQL-layer cycle detection is included (e.g., `AND ',' || p.path_ids || ',' NOT LIKE '%,' || cast(r.target_id as text) || ',%'`) to prevent runaway recursive joins on cyclic structures.
