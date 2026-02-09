# OpenClaw Baseline Research Findings (Phase 1)

**Date**: 2026-02-02
**Subject**: OpenClaw Default Behavior Analysis
**Canon**: `docs/research/openclaw_integration.md`

⸻

## 1.1 Response Generation Analysis

### Pipeline Overview
The OpenClaw response pipeline is a strictly orchestrated procedural loop powered by `pi-embedded-runner`. It does not possess an independent "mind" but rather assembles a temporary persona for each execution.

**Flow:** `UI Event` → `runEmbeddedPiAgent` → `Auth/Context Check` → `Prompt Assembly` → `LLM Execution` → `Response/Tool` → `UI Update`

### Component Breakdown

| Stage | Responsible Component | Mechanism |
| :--- | :--- | :--- |
| **1. Configuration** | `run.ts` | Resolves `SessionLane`, `GlobalLane`, and `AuthProfiles`. Handles cooldowns and failovers (e.g., rotating keys on 429/401). |
| **2. Context Guard** | `context-window-guard.ts` | Checks token limits. Triggers `Compaction` or failures if context is too small. |
| **3. Prompt Assembly** | `system-prompt.ts` | Dynamically builds the System Prompt. Concatenates hardcoded sections: Safety, Tooling, Identity, Time, Skills, Memory, Docs. |
| **4. Execution** | `runEmbeddedAttempt` | Sends request to LLM (Anthropic/OpenAI/etc). Handles retries for specific error types (images, ordering). |
| **5. Tooling** | `pi-tools.ts` | Tools are injected into the LLM context. `exec` tool handles shell commands. |
| **6. Output** | `pi-embedded-subscribe.ts` | Streams chunks to UI. Strips `<think>` tags by default. Handles "Silent Replies". |

### Reasoning Observation
*   **Implicit vs Explicit**: Reasoning is supported via `<think>` tags.
*   **Visibility**: Hidden from user by default (`reasoningLevel: off/hidden`).
*   **Logic**: No inherent multi-step *planning* logic exists in the core loop; it relies on the LLM to choose tools sequentially or the `PlanningAgent` (if used).

⸻

## 1.2 Data Storage & Persistence

OpenClaw uses a **Hybrid Memory System** combining file-system truth with SQLite indexing.

| Data Type | Storage Location | Persistence Strategy | Retention |
| :--- | :--- | :--- | :--- |
| **Chat History** | `sessions/*.json` (implied) | Serialized JSON transcripts. | Permanent (until deletion). |
| **Memory/Knowledge** | `memory/*.md` | Markdown files. | Permanent. Synced to SQLite. |
| **Vector Index** | SQLite (`chunks_vec`) | `sqlite-vec` embeddings of MD files. | Derived cache (rebuilt from files). |
| **Keyword Index** | SQLite (`chunks_fts`) | FTS5 full-text search of MD files. | Derived cache (rebuilt from files). |
| **Session State** | In-Memory / File Sync | Active session state is volatile but checkpoints to disk. | Resilient to restarts (if flushed). |
| **Tool Results** | Chat Transcript | Stored as part of the conversation history. | Permanent. |

**Critical Finding**: Memory is *passive*. Use of memory requires the Agent to explicitly call `memory_search` or `memory_get`. There is no automatic "associative recall" injected into the context window unless configured.

⸻

## 1.3 Learning Limitations

The default OpenClaw system operates as a **Stateless Executor** with a static prompt.

### Why it doesn't learn:
1.  **No Feedback Loop**: Success or failure of a task is recorded in the transcript (history) but never synthesized into *general rules* or *updated strategies*.
2.  **Static Constitution**: Safety rules, tool policies, and behavioral instructions are hardcoded in `system-prompt.ts`. The agent cannot rewrite its own operating procedures based on experience.
3.  **Discarded Signals**:
    *   **Correction patterns**: If a user corrects the agent 10 times on the same mistake, the 11th session starts with the same static prompt.
    *   **Tool Failures**: Repeated failures of a specific tool sequence (e.g., `npm install` failing) are not cached as "strategies to avoid".
    *   **User Preferences**: Unless manually written to `memory/user.md` by the agent (which it rarely does proactively), preferences die with the session context window.

### Discarded Signals List
*   Exception types from tool executions (beyond immediate retry).
*   User sentiment analysis (frustration/joy).
*   Latency/Efficiency metrics of tool chains.
*   "Aha!" moments (successful reasoning paths).

⸻

## Conclusion for Phase 2 Upgrade
To implement **IPPOC**, we must:
1.  **Hijack the Prompt Assembly**: Inject dynamic, learned context *before* `system-prompt.ts` finalizes the string.
2.  **Active Memory Injection**: Replace the passive `memory_search` tool reliance with an auto-retrieved "Hippocampal Context" block.
3.  **The Learning Loop**: Create a post-execution analysis step that writes to `memory/learned_*.md` to update the canonical worldview.
