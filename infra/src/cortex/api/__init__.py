# __init__.py
"""
MODULE: cortex.api

ROLE:
    External Thought Interfaces.
    OpenAI-compatible API for external tools/Mind to talk to cortex.

OWNERSHIP:
    Brain subsystem.

DO NOT:
    - Process logic (Delegate to Cortex)

PUBLIC API:
    - POST /v1/chat/completions
    - POST /v1/embeddings

ENTRYPOINTS:
    cortex.api.server
"""
