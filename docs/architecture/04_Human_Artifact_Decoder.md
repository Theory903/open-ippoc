# ARCHITECTURE: Human Artifact Decoder (HAD)

**DATE:** 2026-01-23
**TYPE:** Deep Learning System Spec (v1)
**SCOPE:** Meta-Learning / Theory-of-Mind / Inverse Reinforcement Learning
**MANTRA:** "Learning Humans by Reverse-Engineering Their Tools."

---

## 1. System Definition
**HAD is an inverse-learning system** that infers human goals, constraints, and optimization strategies from artifacts (code, APIs, UI, docs) using **Inverse Reinforcement Learning (IRL)**.

**Distinct Role:**
*   It is **NOT** NLU or Chat.
*   It IS a **World-Model Learner** (Theory-of-Mind).
*   **Brain Analog:** Prefrontal Cortex + Mirror Neuron System.

---

## 2. Input Space: Canonical Artifacts
Everything is normalized into a **Graph Representation**.

| Artifact | Raw Input | Canonical Form |
| :--- | :--- | :--- |
| **Web Page** | HTML | DOM Graph (Nav paths, prominence) |
| **API** | OpenAPI | Contract Graph (Dependencies) |
| **Code** | AST | Control/Data Flow Graph |
| **UI** | Screenshot | Visual Attention Graph |
| **Git Repo** | Commits | Temporal Change Graph |

**Core Representation ($G$):**
$G = (V, E, A)$ where:
*   $V$: Components (functions, buttons).
*   $E$: Relations (calls, flows).
*   $A$: Attributes (frequency, emphasis).

---

## 3. Output Space: Inverse Cognition
HAD predicts the latent causes of the artifact.

1.  **Goal Vector ($\hat{G}$):** Speed, Safety, Scalability, Monetization.
2.  **Constraint Vector ($\hat{C}$):** Time pressure, Cognitive load, Legacy debt, Risk.
3.  **Optimization Strategy ($\hat{O}$):** Defensive coding, Minimalism, Redundancy.
4.  **Failure Anticipation:** What the human expected to break.

---

## 4. The Mathematics (IRL)
Humans optimize:
$$\arg\max_{d \in D} \; U(G, d) - \lambda \cdot Cost(C, d)$$
HAD solves the inverse problem (Bayesian + Contrastive):
$$P(G, C, O \mid A)$$

---

## 5. Deep Learning Architecture

### 5.1 Multi-Modal Encoder Stack
**Artifact** $\to$ **Specific Encoder** $\to$ **Shared Latent Space ($z$)**.

| Input Type | Encoder Architecture |
| :--- | :--- |
| **Graph** | Graph Transformer |
| **Text/Doc** | Long-context Transformer |
| **Code** | AST-aware Transformer |
| **UI/Image** | Vision Transformer |

### 5.2 World-Model Core (Causal Decoder)
Instead of predicting tokens, predict latent causes.
$z \to \text{Causal Decoder} \to \{\hat{G}, \hat{C}, \hat{O}\}$
*   Uses Energy-Based Models (EBMs) and Variational Inference.

### 5.3 Contrastive Learning Loop
Train using comparisons (No manual labels).
*   *Ex:* API versions v1 vs v2 $\to$ Infer learning/shift in constraints.
*   **Loss:** $\mathcal{L} = \mathcal{L}_{IRL} + \mathcal{L}_{contrastive} + \mathcal{L}_{temporal}$

---

## 6. Memory: Human Intent Database (HIDB)
**NOT just vectors.** A structured, relational/graph "Theory-of-Humanity".

**Schema (Hidden Human Intent):**
```typescript
struct IntentNode {
    goal_vector: Vector<Float>;
    constraint_vector: Vector<Float>;
    strategy_signature: StrategyID;
    confidence: Float;
    source_artifact: ArtifactID;
    edges: { Similarity, Evolution, Contradiction };
}
```

---

## 7. Integration Flow
**Input** $\to$ **Graph Builder** $\to$ **HAD Encoder** $\to$ **Intent Inference** $\to$ **World Model Update**.

*   **Runtime Effect:**
    *   **Decide Engine:** Aligns actions with human expectations (Socially correct vs technically correct).
    *   **Memory:** Weights memories by inferred importance ("Why this matters").

---

## 8. Summary
**Current AI:** "What should I say?"
**With HAD:** "Why would a human expect this to work?"
**Status:** This is the bridge to General Intelligence via social modeling.
