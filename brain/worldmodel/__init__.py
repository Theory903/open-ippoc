# __init__.py
"""
MODULE: brain.worldmodel

ROLE:
    Simulation metaverse for safe testing.

GOVERNANCE:
    Managed by `brain/core/tools/worldmodel.py`.
    DO NOT import specific functions directly.
    USE `ToolOrchestrator` with tool_name="simulation".

PUBLIC API (via Orchestrator):
    - simulation.simulate_action(action)
    - simulation.test_patch(diff_id)
"""
