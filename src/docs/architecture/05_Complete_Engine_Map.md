# ARCHITECTURE: Complete Engine Map (21 Mandatory Engines)

**DATE:** 2026-01-23
**TYPE:** Master System Inventory
**STATUS:** CANONICAL

---

## 🧠 Core Cognitive Engines (The Brain)

1.  **Thalamus Router (Sensory Gate):**
    *   Input priority, interrupt handling, signal routing. (Fast Rule/Light ML).
2.  **Guard & Homeostasis Engine (Brainstem):**
    *   Safety filtering, budget limits, stability enforcement. (Hard constraints).
3.  **Projection Engine (Sensory Cortex):**
    *   Projects text/artifacts $\to$ latent intent space. (Small Neural Nets).
4.  **Uncertainty Engine (Belief Management):**
    *   Tracks Mean + Covariance, propagates uncertainty, Kalman merging. (Pure Math).
5.  **Executive Cortex (PFC):**
    *   Global state, active goals, mode switching. (Deterministic).
6.  **Decision Engine (Control Loop):**
    *   Action generation, Value-Cost-Risk scoring, Policy selection. (Hybrid).
7.  **Active Exploration Engine (Curiosity):**
    *   EIG-driven questioning: $\max(\text{EIG})$. (Decision-theoretic).
8.  **Motor Cortex (Execution):**
    *   Tool execution, LLM calls, Streaming. (No thinking).

---

## 🧠 Memory & Knowledge Engines

9.  **HIDB Storage Engine (Cognitive Memory):**
    *   Intent-centric storage, versioned belief states, decay. (Custom DB).
10. **Memory Retrieval Engine (Recall):**
    *   $O(1)$/$O(\log n)$ paths, Multi-tier recall, Graph-aware.
11. **Memory Consolidation Engine (Sleep):**
    *   Merge, forget, decay, promote salience. (Async).
12. **Meta-Decay Learning Engine (Forgetting Optimizer):**
    *   Learns decay rates $\lambda$ via regret minimization. (Reinforcement).
13. **Knowledge Graph Engine (Association):**
    *   Entity extraction, relations, causal edges. (Symbolic + Vector).

---

## 🤖 Learning & Adaptation Engines

14. **User Understanding Engine (Personal Modeler):**
    *   Knowledge estimation, preference tracking. (Slow learner).
15. **Learn Worker (Plasticity):**
    *   Observes outcomes, reinforces projections. (Fire-and-forget).
16. **Meta-Learning Engine (Tuning):**
    *   Tunes projection nets, calibrates confidence. (Very slow timescale).

---

## 🌐 Human Artifact Intelligence

17. **Human Artifact Decoder (HAD):**
    *   Parses websites/APIs/Docs/UI. Learns from structure. (IRL).
18. **Artifact Abstraction Engine (Symbol Lifter):**
    *   Converts HTML/UI $\to$ Intent Graphs. Normalizes bias.

---

## ⚙️ System & Infrastructure Engines

19. **Cache & Working Memory Engine:**
    *   Session memory, $O(1)$ access (Miller's Law 7$\pm$2). (CPU/RAM).
20. **GPU Scheduler & Execution Engine:**
    *   Batches workloads, orchestrates streams. (Performance).
21. **Observability & Introspection Engine:**
    *   Pipeline tracing, decision explanation, stability monitoring.

---

## Future Extensions (v2+)
22. Neuromorphic / Event-Driven Engine.
23. Self-Evolution Engine.

**Total:** 21 Mandatory Engines.
**Paradigm:** Computational Brain. Not Microservices.
