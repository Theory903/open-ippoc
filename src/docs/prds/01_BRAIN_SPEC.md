# 01_BRAIN_SPEC.md

> **ROLE**: The Dreamer.
> **RESPONSIBILITY**: Reasoning, Planning, Learning, Simulation.

## 1. Architecture
The Brain is a Python-centric subsystem that wraps local LLMs (Phi-4 reasoning) for logic.

### Components
-   **Cortex**: The core reasoning engine.
    -   *Input*: Context, Task.
    -   *Output*: Thought, Plan.
    -   *Model*: `phi-4-reasoning` (Local) or API fallback.
-   **Cerebellum**: Paper-to-Code learner.
    -   *Input*: PDF/ArXiv URL.
    -   *Output*: Python/Rust Implementation.
-   **WorldModel**: Simulation sandbox.
    -   *Input*: Code Proposal, Economic Intent.
    -   *Output*: Predicted Outcome, Risk Score.

## 2. Intelligence Evolution
As per `DOC.md`:
-   **Self-Research**: The Brain reads papers to propose mutations.
-   **Self-Fine-Tuning**: Triggered by persistent failure. Targeted adapters only.

## 3. APIs
The Brain exposes an OpenAI-compatible API at `POST /v1/chat/completions` for the Mind (OpenClaw) to consume.
