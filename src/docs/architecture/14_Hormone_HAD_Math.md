# ARCHITECTURE: Hormone Modulation & HAD Math

**DATE:** 2026-01-23
**TYPE:** Neuromodulation / Input Transduction
**PARADIGM:** Global Modulation of Local Plasticity.

---

## 1. Hormone-Modulated Plasticity
**Concept:** Hormones act as global scalars modifying the learning rate, distinct from data signals.
**Update Rule:**
$$\Delta w_{ij} = \eta \cdot M(h(t)) \cdot \delta_j \cdot x_i$$
**Modulation Function:**
$$M(h(t)) = \sum_k \alpha_k \cdot h_k(t)$$
*   **Dopamine:** Reward Prediction Error ($r - \hat{r}$). Increases $\eta$.
*   **Cortisol:** Stress/Fatigue. Decreases $\eta$.
*   **ACh:** Attention. Opens plasticity window.

---

## 2. Human Artifact Decoder (HAD)
**Role:** Semantic Fuse. Converts raw $I = \{i_1, \dots\}$ into Packets.
**Projection:** $z = \sum_k \beta_k E_k(i_k)$. (Weighted Fusion).
**Output:** Cognitive Packet $\mathcal{P} = \{z, c, u, \tau, h\}$.
*   $z$: Semantic Latent.
*   $h$: Hormone Snapshot (State-dependency).

---

## 3. Neurogenesis (Mathematical)
**Trigger:** Novelty Error.
$$e(t) = \|x(t) - \hat{x}(t)\| > \theta_{novelty}$$
**Growth:** Initialize new neuron $n$ with weight $w_n = x(t)$ and high plasticity $\eta_n$.
**Control:** Prune if Utility $U_n = \mathbb{E}[|a_n|] < \epsilon$.
