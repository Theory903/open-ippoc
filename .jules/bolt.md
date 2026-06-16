## 2024-05-22 - Async File I/O in Synchronous Methods
**Learning:** Even small JSON files (1000 items) can cause significant blocking (23ms) when written synchronously in a tight loop. `dataclasses.asdict` is relatively slow (5ms) but the main bottleneck was redundant disk writes. Offloading to `ThreadPoolExecutor` and removing redundant saves in `tick()` improved performance by 5x (23ms -> 4.7ms).
**Action:** When optimizing "save on every change" patterns, check if intermediate saves (like in `tick`) are necessary and offload the actual I/O to a background thread to unblock the main execution path.

## 2024-05-23 - Synchronous Audit Logging Bottleneck
**Learning:** `ToolOrchestrator._audit_action` was performing synchronous file I/O (open/write/close) for every tool invocation. This introduced ~68ms latency per 1000 calls. Moving this to a background thread with `queue.Queue` reduced it to ~3ms (20x improvement).
**Action:** For high-frequency logging or audit trails, always use an asynchronous writer or background thread to decouple I/O latency from the main execution path.

## 2024-06-25 - Generator Expressions vs Unrolled Loops in Hot Paths
**Learning:** In hot paths (like `AdaptiveRAGRouter._assess_complexity`), using generator expressions with `any()` and inline lists (e.g., `any(word in query for word in ['a', 'b'])`) creates significant overhead due to list recreation and generator function calls. Replacing them with class-level tuple constants and unrolled `for` loops improved execution time by ~3x (1.7s -> 0.6s per 100k iterations).
**Action:** When string substring matching is needed in frequently called methods, hoist invariant lists to class-level tuples and use explicit `for` loops with `break` instead of generator expressions. Do not use tokenized set intersection if exact functional parity (substring matching) must be preserved.
