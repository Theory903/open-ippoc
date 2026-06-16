## 2024-05-22 - Async File I/O in Synchronous Methods
**Learning:** Even small JSON files (1000 items) can cause significant blocking (23ms) when written synchronously in a tight loop. `dataclasses.asdict` is relatively slow (5ms) but the main bottleneck was redundant disk writes. Offloading to `ThreadPoolExecutor` and removing redundant saves in `tick()` improved performance by 5x (23ms -> 4.7ms).
**Action:** When optimizing "save on every change" patterns, check if intermediate saves (like in `tick`) are necessary and offload the actual I/O to a background thread to unblock the main execution path.

## 2024-05-23 - Synchronous Audit Logging Bottleneck
**Learning:** `ToolOrchestrator._audit_action` was performing synchronous file I/O (open/write/close) for every tool invocation. This introduced ~68ms latency per 1000 calls. Moving this to a background thread with `queue.Queue` reduced it to ~3ms (20x improvement).
**Action:** For high-frequency logging or audit trails, always use an asynchronous writer or background thread to decouple I/O latency from the main execution path.

## 2024-05-24 - Expensive Regex Recompilation in RAG Processing
**Learning:** In the `SemanticManager._extract_semantic_components` method, `re.split` and `re.findall` were being called with raw string patterns in a loop over document sentences. This forces Python to compile the regexes on every single method call (or rely on its small internal cache), introducing unnecessary overhead. Compiling regex patterns at the class level and reusing them reduced execution time by approximately 15% during heavy semantic extraction operations.
**Action:** Always hoist invariant regular expressions out of iterative loops and define them as class or module-level compiled constants (`re.compile`) to avoid recompilation overhead.
