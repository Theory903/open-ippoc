# __init__.py
"""
MODULE: brain.evolution

ROLE:
    Self-improvement engine.
    Proposes, validates, and commits mutations (code changes).
    The "Git User" of the organism.

OWNERSHIP:
    Brain subsystem.

DO NOT:
    - Force merge (Must pass tests)
    - Violate Invariants

PUBLIC API:
    - propose_mutation(diff) -> ProposalID
    - review_mutation(id) -> Vote

ENTRYPOINTS:
    brain.evolution.propose
"""
