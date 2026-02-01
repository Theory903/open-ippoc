# ARCHITECTURE: Neural Cognitive System (Blueprint)

**DATE:** 2026-01-23
**TYPE:** Master Architecture (Clean Slate)
**PARADIGM:** Neural Cognitive Architecture with Differentiable Control

---

## 1. Core Design Goal
**From:** Rule-orchestrated intelligence with ML helpers.
**To:** Learned cognitive system with neural control and symbolic execution.
**Maxim:** "Rules may gate. Learning must decide."

---

## 2. Brain → Module Mapping (Canonical)

| Human Brain | Mathematical Role | DL Module | System Component |
| :--- | :--- | :--- | :--- |
| **Thalamus** | Signal gating | Attention Router | **Neural Thalamus** |
| **Sensory Cortex** | Encoding | Encoder Networks | **Input Encoder** |
| **Prefrontal Cortex** | Belief + Planning | World Model | **Executive Model** |
| **Basal Ganglia** | Action Selection | Policy Network | **Action Policy** |
| **Hippocampus** | Episodic Memory | Differentiable Store | **Episodic Store** |
| **Cortex** | Semantic Memory | Learned Embeddings | **Semantic Store** |
| **Cerebellum** | Error Correction | Auxiliary Learners | **Skill Optimizer** |
| **Brainstem** | Reflexes | Rules / Regex | **Reflex Gate** |

---

## 3. Core State Representation ($z_t$)

Replace scalar flags with a learned latent vector:
$$z_t \in \mathbb{R}^{512}$$
Encodes: Intent, Emotion, Uncertainty, Memory Context, Phase, User Style.

**Encoder Stack (Sensory Cortex):**
Multi-encoder fusion (Text Transformer + User Embedding + Context) $\rightarrow$ Projection $\rightarrow z_t$.

---

## 4. The Loop (Layers)

1.  **Input** $\rightarrow$ **Neural Thalamus** (Soft Attention $\alpha = \text{softmax}(W \cdot f)$ over Reflex/Memory/Plan).
2.  **Encoder Stack** $\rightarrow$ Latent State $z_t$.
3.  **World Model (PFC):** Predicts $z_{t+1}$ and future outcomes. Allows planning/rollouts.
4.  **Policy Network (Basal Ganglia):** $\pi(a | z_t) = \text{softmax}(Q(z_t, a))$.
    *   *Training Signal:* Reward (Satisfaction, Success, Latency, Cost).
5.  **Executor (Symbolic Hands):** Validates & executes. **Never learns.**
6.  **Learning Loop:** Updates all modules via 4 losses (Policy, World, Repr, Aux).

---

## 5. Memory System Design (The Quad-Store)

### A. Episodic (Hippocampus)
*   **Storage:** Event-based append-only log.
*   **Usage:** Training data, Replay, Temporal credit assignment.
*   **Consolidation:** Error-based update ($\Delta S = \eta \cdot |\delta|$). "Surprise = Importance."

### B. Semantic (Cortex)
*   **Storage:** Embedding-indexed knowledge.
*   **Retrieval:** Learned attention.

### C. Procedural (Cerebellum)
*   **Storage:** Skill embeddings + properties (success rate, execution graph).

### D. Working Memory (PFC)
*   **Storage:** In-RAM, limited capacity context window.
*   **Eviction:** Learned via attention.

---

## 6. Migration Path

1.  **Phase 1:** Learn $z_t$ (Representation Learning). Keep rules for action.
2.  **Phase 2:** Learn Policy for RESPOND/ASK. Tools still gated.
3.  **Phase 3:** Learn Memory Salience. Replace ranking weights.
4.  **Phase 4:** Introduce World Model & Planning.

---

## 7. Final Truth
The system shifts from an **Advanced Symbolic Architecture** to a **Probabilistic Dynamical System** that learns representations, values, and transitions.
