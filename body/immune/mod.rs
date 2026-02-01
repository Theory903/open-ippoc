// mod.rs
/*!
MODULE: body::immune

ROLE:
    The "White Blood Cells" of the organism.
    Sandbox execution, Code verification, and State Rollback.
    Rejects mutations that violate invariants.

OWNERSHIP:
    Body subsystem.

DO NOT:
    - Bypass safety checks
    - Allow unverified code to run on main thread

PUBLIC API:
    - scan_mutation(diff) -> SafetyScore
    - sandbox_run(code) -> Result
    - rollback(commit_id) -> Result

ENTRYPOINTS:
    body::immune::git_evolution
    body::immune::sandbox
*/
