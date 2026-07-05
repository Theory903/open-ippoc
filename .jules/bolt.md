## 2024-05-22 - Async File I/O in Synchronous Methods
**Learning:** Even small JSON files (1000 items) can cause significant blocking (23ms) when written synchronously in a tight loop. `dataclasses.asdict` is relatively slow (5ms) but the main bottleneck was redundant disk writes. Offloading to `ThreadPoolExecutor` and removing redundant saves in `tick()` improved performance by 5x (23ms -> 4.7ms).
**Action:** When optimizing "save on every change" patterns, check if intermediate saves (like in `tick`) are necessary and offload the actual I/O to a background thread to unblock the main execution path.

## 2024-05-23 - Synchronous Audit Logging Bottleneck
**Learning:** `ToolOrchestrator._audit_action` was performing synchronous file I/O (open/write/close) for every tool invocation. This introduced ~68ms latency per 1000 calls. Moving this to a background thread with `queue.Queue` reduced it to ~3ms (20x improvement).
**Action:** For high-frequency logging or audit trails, always use an asynchronous writer or background thread to decouple I/O latency from the main execution path.

## 2024-05-18 - Optimize dataclasses.asdict serialization
**Learning:** `dataclasses.asdict` is used on hot paths in `EconomyManager` (e.g. `snapshot`, `_save`, `update_tool_stats`). Due to deep copy overhead it costs ~5ms per call. In high-frequency loops or multiple endpoints, this creates measurable latency overhead. Manually constructing dicts reduces time by over 25x (~0.17ms) when state includes nested objects like events and tool stats.
**Action:** Replace `asdict()` with manual `to_dict()` methods on dataclasses heavily accessed in critical I/O paths like the Economy system.
