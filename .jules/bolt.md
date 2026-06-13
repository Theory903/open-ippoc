## 2024-05-22 - Async File I/O in Synchronous Methods
**Learning:** Even small JSON files (1000 items) can cause significant blocking (23ms) when written synchronously in a tight loop. `dataclasses.asdict` is relatively slow (5ms) but the main bottleneck was redundant disk writes. Offloading to `ThreadPoolExecutor` and removing redundant saves in `tick()` improved performance by 5x (23ms -> 4.7ms).
**Action:** When optimizing "save on every change" patterns, check if intermediate saves (like in `tick`) are necessary and offload the actual I/O to a background thread to unblock the main execution path.

## 2024-05-23 - Synchronous Audit Logging Bottleneck
**Learning:** `ToolOrchestrator._audit_action` was performing synchronous file I/O (open/write/close) for every tool invocation. This introduced ~68ms latency per 1000 calls. Moving this to a background thread with `queue.Queue` reduced it to ~3ms (20x improvement).
**Action:** For high-frequency logging or audit trails, always use an asynchronous writer or background thread to decouple I/O latency from the main execution path.

## 2024-05-24 - `dataclasses.asdict` Deepcopy Overhead in High-Frequency Paths
**Learning:** `dataclasses.asdict` recursively performs a deepcopy on all elements within the dataclass, causing severe overhead on nested structures like dictionaries (`~0.27s` for 1000 serializations). This created latency in synchronous execution paths such as `_save` and `snapshot` in `EconomyManager`.
**Action:** Always avoid `dataclasses.asdict` in high-frequency methods. Instead, manually assemble a dict and use shallow `.copy()` operations on simple nested structures to bypass deepcopy overhead, achieving a massive performance gain (up to 100x).
