# ARCHITECTURE: Adaptive Energy-Based Neural Field (AENF)

**DATE:** 2026-01-23
**TYPE:** Adaptive Dynamical Systems / Neurogenesis
**PARADIGM:** Self-Organizing Dynamical Memory with Reversible Growth.

---

## 1. The Core Principle
**Neuron birth is Capacity Management, not Creativity.**
*   Most learning is synaptic (rewiring).
*   New neurons/attractors appear only when the system is stressed (Novelty > Capacity).
*   **Goal:** Expand state space $x(t) \in \mathbb{R}^{N(t)}$ locally and safely.

---

## 2. Requirements for Growth
1.  **Local Learning:** No global backprop.
2.  **Capacity Signal:** Measure interference.
3.  **Energy Constraint:** Growth must reduce system energy ($E(x)$).
4.  **Reversibility:** Pruning is aggressive ($\text{Create} \ll \text{Evaluate} \ll \text{Prune}$).

---

## 3. Creation Conditions
**A. Novelty Error ($\epsilon$):**
Input is not representable by current basis.
$$\epsilon = \|x_{\text{input}} - \hat{x}_{\text{reconstructed}}\| > \epsilon_c$$

**B. Interference Pressure ($P$):**
Existing memories overlap too much (Energy landscape is flat/confused).
$$P = \sum_k \exp(-\beta \|x - \xi^k\|) > P_c$$

**Trigger:** Growth iff $\epsilon > \epsilon_c$ AND $P > P_c$.

---

## 4. The Proto-Neuron Process
**Step 1: Creation**
Create a proto-unit defined by a learned projection of the input:
$$x_{\text{new}} = \phi(u^T x)$$

**Step 2: Local Connection**
Connect only to nearby active neurons (Hebbian initialization):
$$W_{\text{new},j} = \eta \, x_{\text{new}} x_j$$

**Step 3: Stability Check (Lyapunov)**
Evaluate change in system energy $\Delta E$.
*   If $\Delta E < 0$: **Retain** (Stabilizes the field).
*   Else: **Prune** immediately.

---

## 5. Comparison
| System | Grows Units | Stable | Local Learning | Energy-Based |
| :--- | :--- | :--- | :--- | :--- |
| **Standard DL** | ❌ | ❌ | ❌ | ❌ |
| **AENF (HIDB)** | ✅ | ✅ | ✅ | ✅ |

**Conclusion:** AENF allows the HIDB to learn lifelong without catastrophic interference by dynamically expanding its state space.
