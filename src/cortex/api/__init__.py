# __init__.py
"""
MODULE: brain.api

ROLE:
    External Thought Interfaces.
    OpenAI-compatible API for external tools/Mind to talk to Brain.

OWNERSHIP:
    Brain subsystem.

DO NOT:
    - Process logic (Delegate to Cortex)

PUBLIC API:
    - POST /v1/chat/completions
    - POST /v1/embeddings

ENTRYPOINTS:
    brain.api.server
"""
