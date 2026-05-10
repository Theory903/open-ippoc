## 2024-05-22 - Async File I/O in Synchronous Methods
**Learning:** Even small JSON files (1000 items) can cause significant blocking (23ms) when written synchronously in a tight loop. `dataclasses.asdict` is relatively slow (5ms) but the main bottleneck was redundant disk writes. Offloading to `ThreadPoolExecutor` and removing redundant saves in `tick()` improved performance by 5x (23ms -> 4.7ms).
**Action:** When optimizing "save on every change" patterns, check if intermediate saves (like in `tick`) are necessary and offload the actual I/O to a background thread to unblock the main execution path.

## 2024-05-23 - Synchronous Audit Logging Bottleneck
**Learning:** `ToolOrchestrator._audit_action` was performing synchronous file I/O (open/write/close) for every tool invocation. This introduced ~68ms latency per 1000 calls. Moving this to a background thread with `queue.Queue` reduced it to ~3ms (20x improvement).
**Action:** For high-frequency logging or audit trails, always use an asynchronous writer or background thread to decouple I/O latency from the main execution path.

## 2025-05-24 - Generator Expression Overhead in Hot Paths
**Learning:** Using generator expressions with `any(...)` and dynamically recreating lists in frequently called methods like `_assess_complexity` inside `AdaptiveRAGRouter` introduces significant overhead (~1.02s per 10k iterations). Hoisting invariants (`query.lower()`) and unrolling generator expressions using direct `for` loops against class-level tuple constants is ~50% faster (~0.47s). Do NOT replace substring matching with tokenized set intersection (`set(query.split()) & words`) as this breaks functional parity (e.g., matching 'coded' vs 'code').
**Action:** When writing high-frequency routing, parsing, or analysis methods, define static keyword lists as tuple constants and use unrolled `for` loops rather than inline generator expressions.
