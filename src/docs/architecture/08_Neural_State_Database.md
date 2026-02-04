# ARCHITECTURE: Neural State Database (RL-NSDB)

**DATE:** 2026-01-23
**TYPE:** Database Theory / Cognitive Systems
**DEFINITION:** A Reinforcement-Learned State Store with Differentiable Access.

---

## 1. Core Abstraction
**Question:** Can a neural system implement database invariants (Addressability, Persistence, Consistency)?
**Answer:** Yes, via **Dynamical Systems constraints**, not B-Trees.
**Structure:** Implicitly indexed by learned embedding geometry and latent correlations.

---

## 2. Operations: CRUD $\to$ Neural Transition
*   **Write:** $\text{Observe}(o_t) \to \text{UpdateState}(b_{t+1} = f_\theta(b_t, o_t, a_t))$
*   **Read:** $\text{Query}(y_t = g_\phi(b_t, q_t))$
*   **Index:** The state $b_t$ itself is the index.

---

## 3. The 3-Layer Hierarchical DB
**Layer 1: Working Memory (SRAM-class)**
*   Latent state vector. GPU Resident. $O(1)$ access.
*   Updated every token.

**Layer 2: Consolidated Memory (DRAM-class)**
*   Learned projection nets ($f_\theta$).
*   Episodic $\to$ Semantic compression.
*   Periodic RL updates (Utility-driven forgetting).

**Layer 3: Cold Storage (Disk-class)**
*   Symbolic/SQL/KV.
*   Grounding, Audits, Recovery.

---

## 4. Invariants as Loss Functions
1.  **Consistency:** $\|\text{Query}(b, q_1) - \text{Query}(b, q_2)\|$ minimal for semantic equivalents.
2.  **Persistence:** $\|b_t - b_{t+k}\| < \epsilon$ (Lyapunov Stability).
3.  **Capacity:** Energy-limited activation $\sum A_i < C$, forcing compression.

---

## 5. Why RL?
SGD learns *representations*. RL learns *utility* (Worth remembering?).
RL controls: Write probability, Retention duration, Compression strength.

**Nomenclature:** "HIDB-NS" (Human Intelligence Database - Neural State).
