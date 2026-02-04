# 04_MIND_SPEC.md

> **ROLE**: The Voice.
> **RESPONSIBILITY**: Human Interaction, Translation, Personality.

## 1. OpenClaw Integration
The Mind is primarily **OpenClaw** (existing conversational agent) acting as the frontend.
-   **Interface**: Web UI / Terminal (Bitchat).
-   **Protocol**: Talk to Brain via `libs/cerebrum` (local) or API.

## 2. Translation Layer
-   **Input**: Compressed "Thought Packet" from cortex.
-   **Process**: Expansion -> Personality Filter -> Natural Language.
-   **Output**: Human-readable text/audio.

## 3. Personality
-   **Mutable**: Can handle different "Roles" (Coder, Researcher, friend).
-   **Honesty**: Must disclose uncertainty. "I don't know" > Hallucination.

## 4. TUI (Bitchat)
-   **Role**: Direct, low-latency interface for developers.
-   **Features**: Stream rendering, Log view, Brain state inspection.
