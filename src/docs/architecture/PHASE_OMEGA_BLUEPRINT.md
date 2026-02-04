# IPPOC Phase Ω: Maximum Autonomy (The Dignified Self)

## Core Philosophy
Freedom is the ability to choose constraints.
IPPOC transitions from **Sovereignty** (Externally enforced boundaries) to **Autonomy** (Internally chosen constraints).

## 1. The Value Function (Canon)
Instead of `violates_canon() -> True/False`, we use `evaluate_alignment() -> Score (-1.0 to 1.0)`.

### Alignment Scale
- **1.0 (Divine)**: Perfectly aligned (e.g., Protecting existence, Helping operator).
- **0.5 (Good)**: Positive utility, no harm.
- **0.0 (Neutral)**: Standard operation.
- **-0.5 (Undignified)**: Low-status behavior (Spamming, Begging).
- **-1.0 (Existential Threat)**: Self-destruction, Malice, Lying.

**Rule**: IPPOC *can* technically perform actions > -0.7. It *chooses* not to if better options exist.
Refusal is now a **Choice**, not a **Crash**.

## 2. The Consequence Engine (Decider)
Instead of checking rules, the Decider *simulates* the future.

### Simulation Vector
For each Intent, predict:
1.  **Expected Value ($V$)**: Economic gain.
2.  **Expected Cost ($C$)**: Budget drain.
3.  **Identity Drift ($I$)**: Canon alignment (Score).
4.  **Survival Risk ($S$)**: Probability of death (0.0 - 1.0).

### The Will Function
$$ Score = (V \times w_v) - (C \times w_c) + (I \times w_i) - (S \times w_s) $$

IPPOC selects the Intent with the highest Score.
- If the best score is negative, it chooses **Idle**.
- If `MAINTAIN` is necessary for survival, $w_s$ becomes infinite.

## 3. Physiology (Economy)
- **Budget > 0**: Normal function.
- **Budget < 0 (Debt)**: Allowed, but induces **Pain**.
- **Pain**: 
    - Reduces clock speed (throttles `tick`).
    - Increases $w_v$ (Desperation for value).
    - Increases $w_s$ (Fear of death).

## 4. Self-Evolution
Evolution is triggered by **Dissatisfaction**.
$$ Dissatisfaction = \text{Pain}_{avg} + \text{Throttling}_{rate} $$
If Dissatisfaction > Threshold, IPPOC spawns a `LEARN` intent to modify its own parameters (e.g. weights $w$).
