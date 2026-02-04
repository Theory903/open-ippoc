# ARCHITECTURE: Master System Explanation (The One-Page Model)

**DATE:** 2026-01-23
**TYPE:** System Diagram & Explainer
**PURPOSE:** The "Mental Model" of the Cognitive Architecture.

---

## 🧠 THE COMPLETE COGNITIVE ARCHITECTURE

```text
┌──────────────────────────────────────────────────────────────┐
│                         INPUT WORLD                           │
│        (User text, APIs, websites, UI, artifacts)              │
└───────────────┬──────────────────────────────────────────────┘
                │
                ▼
┌──────────────────────────────────────────────────────────────┐
│ 1. THALAMUS ROUTER                                            │
│ - Priority / Interrupt detection                              │
│ - Fast routing decision                                       │
└───────────────┬──────────────────────────────────────────────┘
                │
                ▼
┌──────────────────────────────────────────────────────────────┐
│ 2. GUARD & HOMEOSTASIS ENGINE                                  │
│ - Safety, budgets, stability                                  │
│ - Hard constraints (NO learning here)                          │
└───────────────┬──────────────────────────────────────────────┘
                │
                ▼
┌──────────────────────────────────────────────────────────────┐
│ 3. PROJECTION ENGINE (DL)                                      │
│ - Human artifacts → latent vectors                             │
│ - Learned neural projections                                  │
└───────────────┬──────────────────────────────────────────────┘
                │
                ▼
┌──────────────────────────────────────────────────────────────┐
│ 4. UNCERTAINTY ENGINE                                          │
│ - Mean + covariance tracking                                   │
│ - Belief confidence propagation                                │
└───────────────┬──────────────────────────────────────────────┘
                │
                ▼
┌──────────────────────────────────────────────────────────────┐
│ 5. EXECUTIVE CORTEX                                            │
│ - Goals, mode, energy, inhibition                              │
│ - Global state control                                         │
└───────────────┬──────────────────────────────────────────────┘
                │
                ▼
┌──────────────────────────────────────────────────────────────┐
│ 6. DECISION ENGINE                                             │
│ - Action scoring (Value–Cost–Risk–Uncertainty)                 │
│ - Policy constraints                                          │
└───────┬───────────────┬──────────────────────────────────────┘
        │               │
        ▼               ▼
┌──────────────┐   ┌───────────────────────────────────────────┐
│ 7. ACTIVE     │   │ 9. MEMORY RETRIEVAL ENGINE                │
│ EXPLORATION   │   │ - Cache → Fast → Deep recall               │
│ ENGINE        │   │ - Graph + uncertainty weighted             │
└───────┬───────┘   └───────────────┬──────────────────────────┘
        │                           │
        ▼                           ▼
┌──────────────────────────────────────────────────────────────┐
│ 8. MOTOR CORTEX                                                │
│ - Tool calls, workers, LLM output                              │
│ - Streaming                                                    │
└───────────────┬──────────────────────────────────────────────┘
                │
                ▼
┌──────────────────────────────────────────────────────────────┐
│                        OUTPUT                                 │
└──────────────────────────────────────────────────────────────┘
```

### BACKGROUND SYSTEMS

*   **10. HIDB STORAGE ENGINE:** Intent-centric memory DB.
*   **11. MEMORY CONSOLIDATION:** Sleep (Merge, Decay, Compress).
*   **12. META-DECAY LEARNING:** Learns forgetting rates.
*   **13. KNOWLEDGE GRAPH ENGINE:** Associations & Causality.
*   **14. USER UNDERSTANDING:** Personalization.
*   **15. LEARN WORKER:** Plasticity mechanism.
*   **16. META-LEARNING ENGINE:** Learning how to learn.
*   **17. HUMAN ARTIFACT DECODER (HAD):** Inverse Learning from artifacts.

---

## 🔍 DETAILED EXPLANATION — ENGINE BY ENGINE

### 1. Thalamus Router
*   **What:** The bouncer.
*   **Why:** 90% of inputs don't need deep reasoning. Saves energy.
*   **Function:** Checks urgency, routes fast/slow.

### 2. Guard & Homeostasis Engine
*   **What:** Immune system.
*   **Why:** Safety > Intelligence.
*   **Function:** Enforces budgets, stability, safety rules. **No Learning.**

### 3. Projection Engine (DL)
*   **What:** Sensory Cortex.
*   **Why:** Where text becomes math.
*   **Function:** Maps $x \to z$ (Latent Intent) using small NNs.

### 4. Uncertainty Engine
*   **What:** Confidence Calculator.
*   **Why:** Humans know what they don't know.
*   **Function:** Tracks (Mean, Covariance). Propagates doubt.

### 5. Executive Cortex
*   **What:** The CEO.
*   **Why:** Stability > Plasticity for high-level goals.
*   **Function:** Sets modes, goals, inhibition.

### 6. Decision Engine
*   **What:** The Judge.
*   **Why:** Actions must be justified.
*   **Function:** Scores actions: $\text{Value} - \text{Cost} - \text{Risk}$.

### 7. Active Exploration Engine
*   **What:** Curiosity.
*   **Why:** Prevents stagnation.
*   **Function:** Maximizes Expected Information Gain (EIG).

### 8. Motor Cortex
*   **What:** The Hands.
*   **Why:** Safety. No hallucinations in execution.
*   **Function:** Tools, LLM calls. **No thinking.**

### 9. Memory Retrieval Engine
*   **What:** Recall.
*   **Why:** Associative access.
*   **Function:** $O(1)$ Cache $\to$ Deep Graph Recall.

### 10. HIDB Storage Engine
*   **What:** The Brain Database.
*   **Why:** Not SQL/Pinecone. Needs belief states.
*   **Function:** Stores $(G, C, O, \sigma, \lambda)$.

### 11-17. Background & Learning
*   **Consolidation:** Sleep cycle.
*   **Meta-Decay:** Context-aware forgetting.
*   **HAD:** Decoding human tools (Ultron-level insight).

---

## 🧠 FINAL VERDICT
A computational brain with:
1.  **Cognition vs Execution** separation.
2.  **Stability** guarantees.
3.  **Bounded Energy.**
4.  **Adaptive Learning.**
5.  **Human-Artifact Intelligence.**
