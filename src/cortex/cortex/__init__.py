# __init__.py
"""
MODULE: cortex.cortex

ROLE:
    Deep reasoning engine (LLM Logic).
    Handles complex thought chains, math, and coding logic.
    Uses 'Phi-4-reasoning' or similar models.

OWNERSHIP:
    Brain subsystem.

DO NOT:
    - Execute code (Delegate to WorldModel sandbox)
    - Memorize directly (Delegate to Memory API)

PUBLIC API:
    - reason(prompt) -> Conclusion
    - solve(problem) -> Solution

ENTRYPOINTS:
    cortex.cortex.think
"""
