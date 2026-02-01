# ARCHITECTURE: IPPOC-DL v2 (Clean Slate)

**DATE:** 2026-01-23
**TYPE:** Master Architecture (v2)
**PARADIGM:** Brain-Inspired, Deep-Learning-First, Energy-Optimal

---

## 0. Design Axioms (Non-Negotiable)
1.  **Energy > FLOPs:** Minimize memory movement.
2.  **Hot paths must be O(1):** Hash / Table / Bitset.
3.  **Learning replaces rules:** Rules are scaffolding.
4.  **Asynchronous by default:** Non-blocking critical path.
5.  **State is continuous:** Latent state transitions ($S_t \to S_{t+1}$), not symbolic if/else.

---

## 1. Macro View (The Feedback Loop)
**Input** $\to$ **Thalamus-NN** (Learned Router) $\to$ **Cortex Core** (World RNN) $\to$ **Policy Net** (Action Selection) $\to$ **Motor Layer** (Execution) $\to$ **Learning Sys** (Async).

*Paradigm:* Closed feedback learner, not a request-response pipeline.

---

## 2. Core Representation: World State Vector ($S_t$)
Replace symbolic flags with a continuous latent vector:
$$S_t \in \mathbb{R}^{1024}$$
*   **Encodes:** User intent, urgency, emotion, phase, task progress, confidence.
*   **Transition:** $S_{t+1} = f_\theta(S_t, X_t, M_t)$ (GRU/RWKV/SSM).

---

## 3. Engine Map (DL-First Components)

### 3.1 Thalamus-NN (Learned Router)
*   **Role:** Ultra-fast routing + interrupt detection.
*   **Model:** Tiny MLP / Linear Probe (INT8, < 50µs).
*   **Output:** Urgency, Complexity, Risk, MemoryNeed.

### 3.2 Cortex Core (World Model)
*   **Role:** Track trajectory, maintain goals, predict next useful action.
*   **Model:** RWKV / SSM / GRU + Attention.

### 3.3 Memory System (Custom DB Structure)
**Layer 1: Hash Memory (O(1))**
*   Learned binary hash ($h = g(x) \in \{0,1\}^{64}$).
*   Key $\to$ Pointer. Instant recall.

**Layer 2: Vector Slab**
*   Contiguous memory, PQ-compressed, GPU-friendly.

**Layer 3: Cold Archive**
*   Disk-based, async only.

**Retrieval Logic:** Hash $\to$ Bucket $\to$ Small Attention ($|B| \le 32$).

### 3.4 Policy Network (Basal Ganglia)
*   **Input:** $S_t$.
*   **Output:** $\pi(a|S_t)$ (Respond, Tool, Search, Ask, Think, Wait).
*   **Reward:** $R = \text{Usefulness} - \text{Latency} - \text{Cost} - \text{Risk}$.

### 3.5 Motor Layer
*   **Role:** Deterministic execution kernel (Safety/Auditing). **Non-ML.**

---

## 4. Hardware Optimization (Brain-Like)
*   **CPU (Control):** HTTP, Hashing, Scheduling, DB I/O.
*   **GPU (Data):** Embeddings, World Model, Policy, Ranking.
*   **Optimization:** CUDA streams per module, Fixed encodings (no branching).

---

## 5. Learning System
*   **Online:** Preference tuning, Style adaptation (LoRA / EMA).
*   **Offline (Sleep):** Consolidate memories, retrain hash functions, compress representations.

## 6. Definitions of Intelligence
"The system is a dynamical system minimizing surprise under energy constraints."
