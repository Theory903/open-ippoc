# ARCHITECTURE: World Model Memory (Weights = Memory)

**DATE:** 2026-01-23
**TYPE:** Paradigm Shift / Advanced Memory Theory
**DEFINITION:** "A true memory system does not store information — it reshapes itself so future information becomes predictable."

---

## 1. The Core Shift
**From:** Database View (Store, Retrieve, Rank).
**To:** World Model View (Observe, Update, Predict).
*   **Vector DB:** Static, explicit, external.
*   **World Model:** Dynamic, implicit, internal.
*   **Maxim:** "Weights ARE the memory."

---

## 2. Correct Abstraction: Memory = Learned Compression
**Brain Analogy:** The brain compresses experience into invariants.
**Math:** Minimum Description Length (MDL).
$$\min_\theta \; L(\theta) + L(D \mid \theta)$$
*   $\theta$: Memory (weights).
*   $D$: Observed world.

---

## 3. Core Architecture (The 4 Components)

### 1. Encoder (Perception)
Turns artifacts into latent signals.
$$h_t = E_\theta(o_t)$$

### 2. Memory Core (Pattern Accumulator)
Integrates over time, forgets noise. Online learning.
$$m_{t+1} = m_t + \alpha \cdot \nabla_\theta \log P(o_t \mid m_t)$$

### 3. Dynamics (World Model)
Learns relationships, reasoning, analogy.
$$z_{t+1} = F_\theta(z_t)$$

### 4. Decoder (Expression)
Converts latent state to answers/actions.
$$\hat{o}_{t+1} = D_\theta(z_t)$$

---

## 4. Latent Attractor Fields
Memory is not a table, but a **High-Dimensional Energy Landscape**.
*   **Valleys:** Concepts.
*   **Basins:** Beliefs.
*   **Retrieval:** Falling into the right basin ($\dot{z} = -\nabla E(z)$).

---

## 5. Training Signals (Not Labels)
1.  **Prediction Loss:** $-\log P(o_{t+1} \mid z_t)$.
2.  **Consistency Loss:** Same concept $\to$ Same latent region.
3.  **Compression Pressure:** Penalize complexity.
4.  **Stability Loss:** Prevent catastrophic drift.

---

## 6. Contrast with LLMs
*   **LLM:** Static, frozen, batch-trained.
*   **World Model Memory:** Online, adaptive, personal, continuous learning.

**Target System:** A **Predictive Coding System** / **Continual World Model**. Not a RAG pipeline.
