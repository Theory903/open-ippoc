# ARCHITECTURE: Cognitive Neural System (CNS)

**DATE:** 2026-01-23
**TYPE:** Next-Gen Architecture / Brain-Inspired Computing
**PARADIGM:** Dynamical, Plastic, Multi-Timescale System (Beyond Standard DL)

---

## 1. The Core Shift
**From:** Modern NNs (Static function approximators: $y = f_\theta(x)$).
**To:** Biological Analogs (Living dynamical systems: $\tau \frac{dV}{dt} = -V + \dots$).
**Key Difference:** Learning is continuous, local, and event-driven. Time is a first-class citizen.

---

## 2. Five Pillars of CNS
1.  **Time as First-Class:** $x_t \to x_{t+1}$. Recurrent dynamics, no reset.
2.  **Multiple Memory Types:**
    *   *Working:* Fast activations.
    *   *Plastic:* Fast weights (Hebbian).
    *   *Long-Term:* Slow weights (SGD).
3.  **Local Learning:** No global backprop. $\Delta w \propto \text{pre} \times \text{post}$ (Hebbian/Predictive Coding).
4.  **Sparse, Event-Driven:** O(1) energy efficiency. Spike when necessary.
5.  **Self-Regulation:** Homeostasis. Bounded activations prevents explosion.

---

## 3. The 6-Layer Architecture

### Layer 1: Sensory Encoder
*   **Role:** Input $\to$ Latent Signal.
*   **Math:** $h_t = E(x_t)$.

### Layer 2: Working Memory (Fast State)
*   **Role:** Volatile attention-based state.
*   **Math:** $s_{t+1} = f(s_t, h_t)$.

### Layer 3: Plastic Memory (Mid-Speed)
*   **Role:** Temporary associations (Fast Weights).
*   **Math:** $W_t = W_{t-1} + \alpha g_t$.

### Layer 4: Long-Term Memory (Slow Weights)
*   **Role:** Consolidated patterns.
*   **Math:** $\theta_{t+1} = \theta_t + \eta_t \Delta \theta$.

### Layer 5: World Model
*   **Role:** Prediction & Causality.
*   **Math:** $\hat{h}_{t+1} = F(h_t, a_t)$.

### Layer 6: Controller / Gating
*   **Role:** Decides what to learn/ignore.
*   **Math:** $g_t = \sigma(W[h_t, s_t])$.

---

## 4. Training Paradigm
Cannot be trained like GPT (Next Token only).
1.  **Self-Supervised Prediction:** Minimize surprise ($x_{t+1} - \hat{x}_{t+1}$).
2.  **Reinforcement Learning:** Reward = Reduced Uncertainty. Penalty = Instability.
3.  **Continual Learning:** No epochs, no dataset boundaries. Experience Replay.
4.  **Meta-Learning:** Learning how fast to learn (Adaptive $\eta$).

---

## 5. Feasibility
**Theoretically:** Superior to Feedforward DL (Learns continuously, builds internal models).
**Practically:** Hard (Unstable). Requires rigorous math (Lyapunov) and careful engineering.
**Closest Relatives:** MuZero, Predictive Coding, Active Inference (Friston).
