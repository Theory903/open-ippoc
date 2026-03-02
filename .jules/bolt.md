## 2024-05-22 - Async File I/O in Synchronous Methods
**Learning:** Even small JSON files (1000 items) can cause significant blocking (23ms) when written synchronously in a tight loop. `dataclasses.asdict` is relatively slow (5ms) but the main bottleneck was redundant disk writes. Offloading to `ThreadPoolExecutor` and removing redundant saves in `tick()` improved performance by 5x (23ms -> 4.7ms).
**Action:** When optimizing "save on every change" patterns, check if intermediate saves (like in `tick`) are necessary and offload the actual I/O to a background thread to unblock the main execution path.

## 2024-05-23 - Synchronous Audit Logging Bottleneck
**Learning:** `ToolOrchestrator._audit_action` was performing synchronous file I/O (open/write/close) for every tool invocation. This introduced ~68ms latency per 1000 calls. Moving this to a background thread with `queue.Queue` reduced it to ~3ms (20x improvement).
**Action:** For high-frequency logging or audit trails, always use an asynchronous writer or background thread to decouple I/O latency from the main execution path.

## 2024-05-24 - N+1 Sequential API Calls in RAG Implementations
**Learning:** During the retrieval and reranking phase in RAG (e.g. HyDE RAG), scoring documents sequentially using an external model or API (`aembed_documents` in a `for` loop) causes an N+1 bottleneck. This results in heavy latency penalties due to multiple network round-trips when N documents are retrieved.
**Action:** Always inspect loops in document retrieval and reranking phases. Gather the necessary payloads (e.g. document contents) and use batched API calls to transform O(N) network requests into an O(1) batched request, thereby drastically reducing latency and improving throughput.
