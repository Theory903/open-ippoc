## 2024-05-22 - Async File I/O in Synchronous Methods
**Learning:** Even small JSON files (1000 items) can cause significant blocking (23ms) when written synchronously in a tight loop. `dataclasses.asdict` is relatively slow (5ms) but the main bottleneck was redundant disk writes. Offloading to `ThreadPoolExecutor` and removing redundant saves in `tick()` improved performance by 5x (23ms -> 4.7ms).
**Action:** When optimizing "save on every change" patterns, check if intermediate saves (like in `tick`) are necessary and offload the actual I/O to a background thread to unblock the main execution path.

## 2024-05-23 - Synchronous Audit Logging Bottleneck
**Learning:** `ToolOrchestrator._audit_action` was performing synchronous file I/O (open/write/close) for every tool invocation. This introduced ~68ms latency per 1000 calls. Moving this to a background thread with `queue.Queue` reduced it to ~3ms (20x improvement).
**Action:** For high-frequency logging or audit trails, always use an asynchronous writer or background thread to decouple I/O latency from the main execution path.
## 2025-05-25 - Avoid `dataclasses.asdict` in high-frequency serialization paths
**Learning:** In IPPOC's `EconomyManager`, serialization is triggered frequently (e.g., on every `spend()` event) and executed in a separate thread. Calling `dataclasses.asdict(self.state)` is extremely slow (taking ~5-6ms per call) because it performs a deepcopy of the entire structure (which includes growing lists of events and nested dictionaries for tools). This causes high overhead in a fast-path operation.
**Action:** When a dataclass has nested structures or requires frequent serialization to JSON, use a manual dictionary construction instead of `dataclasses.asdict()`. A manual mapping with shallow `.copy()` for nested components speeds up serialization by ~20x.
