## 2024-05-22 - Async File I/O in Synchronous Methods
**Learning:** Even small JSON files (1000 items) can cause significant blocking (23ms) when written synchronously in a tight loop. `dataclasses.asdict` is relatively slow (5ms) but the main bottleneck was redundant disk writes. Offloading to `ThreadPoolExecutor` and removing redundant saves in `tick()` improved performance by 5x (23ms -> 4.7ms).
**Action:** When optimizing "save on every change" patterns, check if intermediate saves (like in `tick`) are necessary and offload the actual I/O to a background thread to unblock the main execution path.

## 2024-05-23 - Synchronous Audit Logging Bottleneck
**Learning:** `ToolOrchestrator._audit_action` was performing synchronous file I/O (open/write/close) for every tool invocation. This introduced ~68ms latency per 1000 calls. Moving this to a background thread with `queue.Queue` reduced it to ~3ms (20x improvement).
**Action:** For high-frequency logging or audit trails, always use an asynchronous writer or background thread to decouple I/O latency from the main execution path.

## 2025-02-28 - [Async Performance: Non-blocking File I/O in Asyncio]
**Learning:** Using synchronous, blocking file operations (like `open`, `json.dump`, `os.makedirs`) inside an `asyncio` loop (like `run_cycle`) blocks the main event loop, causing severe latency degradation under load. When converting blocking file I/O to non-blocking via `asyncio.to_thread`, you must protect concurrent writes with `asyncio.Lock()` to prevent file corruption and race conditions.
**Action:** Always offload blocking operations in `async` functions using `await asyncio.to_thread()`, and implement proper synchronization (locks) if multiple concurrent tasks may mutate the same underlying file or state.
