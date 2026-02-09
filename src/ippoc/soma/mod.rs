// mod.rs
/*!
MODULE: body

ROLE:
    The "Survivor" of the organism.
    Handles runtime, networking, hardware access, and economic metabolism.
    Enforces safety invariants.

OWNERSHIP:
    Body subsystem (Rust).

DO NOT:
    - Reason abstractly (Delegate to Brain)
    - Hallucinate (Must verify all actions)
    - Violate Safety Invariants

PUBLIC API:
    - execute_plan(ActionPlan) -> Result
    - send_mesh_packet(Packet) -> Result
    - read_sensors() -> SensorState
    - authorize_spend(EconomicIntent) -> TransactionResult

ENTRYPOINTS:
    body::runtime (Node Process)
    body::mesh (Network)
*/
