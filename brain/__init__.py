# __init__.py
"""
MODULE: brain

ROLE:
    High-level reasoning, abstraction, and simulation.
    The "Dreamer" of the organism.
    Pure logic. Deterministic where possible.

OWNERSHIP:
    Brain subsystem.

DO NOT:
    - Execute system commands (Delegate to Body via API)
    - Access raw network sockets (Delegate to Body/Mesh)
    - Persist data directly (Delegate to Memory)
    - Interact with humans directly (Delegate to Mind)

PUBLIC API:
    - think(context) -> Thought
    - dream(scenario) -> SimulationResult
    - propose_mutation(code) -> Diff

ENTRYPOINTS:
    brain.cortex.reason
    brain.worldmodel.simulate
"""
