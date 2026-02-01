# __init__.py
"""
MODULE: brain.cerebellum

ROLE:
    Paper-to-Code learning engine.
    Ingests research papers and translates them into executable code proposals.
    The "Research Assistant" lobe.

OWNERSHIP:
    Brain subsystem.

DO NOT:
    - Deploy code (Delegate to Evolution)
    - Access production DB

PUBLIC API:
    - digest_paper(pdf_url) -> CodeProposal
    - learn_skill(topic) -> SkillUpdate

ENTRYPOINTS:
    brain.cerebellum.digest
"""
