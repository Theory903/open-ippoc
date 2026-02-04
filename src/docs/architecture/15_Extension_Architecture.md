# HIDB Extension Architecture

**Goal**: Allow third parties to add skills, tools, planners, and agents without violating cognitive invariants.

The system must remain:
*   Non-hallucinatory
*   Veto-safe
*   Auditable
*   Deterministic under arbitration

## The One Law of Extensibility
**Third parties may extend capability, never authority.**
Authority remains inside HIDB’s core experts.

## Layered Model

```text
┌──────────────────────────────┐
│  External World (APIs, Tools)│
└──────────────┬───────────────┘
               │
┌──────────────▼───────────────┐
│  TOOLS (MCP / Plugins)       │  ← unsafe by default
└──────────────┬───────────────┘
               │
┌──────────────▼───────────────┐
│  SKILLS (Composed Logic)     │  ← safe, declarative
└──────────────┬───────────────┘
               │
┌──────────────▼───────────────┐
│  PLANNERS (Strategies)       │
└──────────────┬───────────────┘
               │
┌──────────────▼───────────────┐
│  EXPERTS (Authority)         │  ← NEVER extensible
└──────────────┬───────────────┘
               │
┌──────────────▼───────────────┐
│  ARBITRATION CORE (HIDB)     │
└──────────────────────────────┘
```

## 1. Tools (MCP Integration Layer)
Tools are not intelligence. They are unsafe actuators.

### Key Rules
*   Tools cannot decide
*   Tools cannot plan
*   Tools cannot self-invoke
*   Tools must be wrapped in outcomes

**MCP Mapping**: MCP handles *how* to call. HIDB handles *whether* to call.

## 2. Skills (Composable, Declarative)
A Skill is not an agent. It is a named composition of plans + tools + constraints.

```rust
pub struct Skill {
    pub name: String,
    pub required_tools: Vec<ToolId>,
    pub preconditions: Vec<Constraint>,
    pub postconditions: Vec<Constraint>,
}
```

Skills are recipes, not cooks.

## 3. Planners (Strategy Providers)
Planners decide how to use skills. They are replaceable, pluggable, sandboxed.

```rust
pub trait Planner {
    fn propose_plan(&self, goal: Goal, skills: &[Skill], ctx: &CognitiveContext) -> Vec<Plan>;
}
```

**Constraint**: Planners never execute, never approve.

## 4. Agents (Thin Orchestration)
An Agent is just wiring. It contains zero intelligence.

```rust
loop {
    ctx = observe();
    plans = planner.propose(ctx);
    result = arbiter.arbitrate(plans);
    if approved {
        execute();
        record_outcome();
    }
}
```

## 5. Experts (NON-EXTENSIBLE)
Experts (Verifier, Safety, Memory, Identity, Proposer) are the hard line.
*   No third-party experts.
*   No plugins.
*   No overrides.

## 6. Arbitration (Immutable Core)
Every external addition flows through: **Skill → Plan → Expert Veto → Execute or Die**.

## 7. How Third Parties Add Value
**CAN Add**: Tools, Skills, Planners, UI agents, Simulators, Sensors.
**CANNOT Add**: Approval logic, Memory mutation, Identity rules, Safety overrides.

## 8. Performance & Hardware
*   **CPU**: Arbitration, Planning, Logic.
*   **GPU**: LLM Proposer, Embeddings, Physics.
*   **Async**: Tool execution, MPC calls.

## Final Truth
**LLMs answer questions. HIDB governs decisions.**
