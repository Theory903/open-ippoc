## 2024-05-22 - Async File I/O in Synchronous Methods
**Learning:** Even small JSON files (1000 items) can cause significant blocking (23ms) when written synchronously in a tight loop. `dataclasses.asdict` is relatively slow (5ms) but the main bottleneck was redundant disk writes. Offloading to `ThreadPoolExecutor` and removing redundant saves in `tick()` improved performance by 5x (23ms -> 4.7ms).
**Action:** When optimizing "save on every change" patterns, check if intermediate saves (like in `tick`) are necessary and offload the actual I/O to a background thread to unblock the main execution path.

## 2024-05-23 - Synchronous Audit Logging Bottleneck
**Learning:** `ToolOrchestrator._audit_action` was performing synchronous file I/O (open/write/close) for every tool invocation. This introduced ~68ms latency per 1000 calls. Moving this to a background thread with `queue.Queue` reduced it to ~3ms (20x improvement).
**Action:** For high-frequency logging or audit trails, always use an asynchronous writer or background thread to decouple I/O latency from the main execution path.

## 2024-07-28 - Dataclass Serialization Overhead in High-Frequency Paths
**Learning:** `dataclasses.asdict` performs a deep copy of all fields, which can be surprisingly slow (~2ms per call) for nested structures. In high-frequency paths like `EconomyManager` (which logs tools and checks budgets continuously), this adds significant latency. Manually constructing a dictionary and using shallow `.copy()` for nested lists/dicts is ~500x faster (~0.003ms) and avoids the deep-copy overhead.
**Action:** When optimizing performance-critical data serialization in Python, avoid `dataclasses.asdict` unless a true deep copy is required. Manually mapping fields and using shallow copies for nested states is drastically faster for simple state snapshots.
