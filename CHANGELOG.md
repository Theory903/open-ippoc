# Changelog

All notable changes to the IPPOC project will be documented in this file.

## [v1.0.0-alive] - 2026-02-03
### Frozen
- **Genome**: `brain/core/genome.py` captures Identity DNA (`GENOME.json`).
- **Dependencies**: `requirements.lock` pins environment.
- **Canon**: Reinforced against self-destruction ("destroy self").
- **Identity**: Cryptographically hashed and broadcast in `FEDERATION_BROADCAST.md`.

## [v0.11.0-market] - 2026-02-03
### Added
- **Market Contracts**: `brain/market/contracts.py` defines `ExternalWorkUnit`.
- **Evaluator**: `brain/market/evaluator.py` implements the Dignity Filter (Will Score).
- **Dignity Floor**: IPPOC refuses `Alignment <= -0.5` work regardless of Reward or Starvation.
- **Verification**: `verify_market_presence.py` certifies economic sovereignty.

## [v0.10.0-delegated] - 2026-02-03
### Added
- **Cognitive Cell**: `brain/core/delegation.py` implements non-sovereign sub-agents.
- **Contract Enforcement**: Cells are bound by strict Scope, Budget, and TTL.
- **Supervisor Loop**: `AgencyManager.audit_cells()` terminates inefficient or rogue cells.
- **Verification**: `verify_delegated_agency.py` certifies scalable, safe delegation.

## [v0.9.0-federated] - 2026-02-03
### Added
- **Federation Identity**: `brain/core/federation.py` implements Node Identity & Signals.
- **Consultation Protocol**: `IntentType.CONSULT` allows advice exchange.
- **Reputation Engine**: `brain/social/reputation.py` tracks peer reliability.
- **Social Will**: Decider now weighs Advice ($Reputation \times Confidence$) in Will Score.
- **Verification**: `verify_federation.py` certifies Social Agency.

## [v0.8.0-autonomous] - 2026-02-03
### Transformed
- **Canon**: Converted from Policy Gate to **Value Function** (`evaluate_alignment` returns -1.0 to 1.0).
- **Decider**: Converted to **Consequence Engine** (`Will Function` balances ROI + Alignment - Cost - Risk).
- **Economy**: Replaced Hard Stops with **Physiology** (`Pain` reduces frequency, forces conservation).
- **Verification**: `verify_autonomous_will.py` certifies that IPPOC *chooses* right, rather than obeying rules.

## [v0.7.0-earner] - 2026-02-03
### Added
- **Work Contracts**: `brain/core/contract.py` implements `WorkUnit` primitive.
- **Foraging Adapter**: OpenClaw actions can now propose contracts (`propose_contract`).
- **Desperation Logic**: Starving IPPOC accepts high-risk/low-cost contracts even if budget is critical.
- **Verification**: `verify_real_foraging.py` certifies contract lifecycle.

## [v0.6.0-foraging] - 2026-02-03
### Added
- **ROI Engine**: Economy now tracks tool Value, Confidence, and ROI.
- **Budget Foraging**: Budget regenerates only via `record_value` (Formula: `Value * Confidence * Decay`).
- **Autonomy Upgrade**: Planner/Decider prioritize High-ROI intents and idle on Low-ROI.
- **Throttling**: Tools with negative ROI are automatically throttled.
- **Vitals Update**: Exposed Economic stats (ROI, Total Value) in `vitals.py`.

## [v0.5.0-observable] - 2026-02-03
### Added
- **Operator Experience**: Enabled `vitals` and `timeline` endpoints for UI.
- **Refusal History**: Sovereignty refusals are now queryable via API.

## [v0.4.0-connected] - 2026-02-03
### Added
- **OpenClaw Bridge**: Implemented `brain/gateway/` to adapt OpenClaw actions into IPPOC Intents.
- **Neural Guard**: Pre-emptive Canon checking in `openclaw_guard.py` before cognition.
- **Organ Mapping**: `openclaw_plugin_map.py` deterministically maps plugins (shell, db) to organs (body, memory).
- **Throttling**: Added `should_throttle()` to `EconomyManager`.

## [v0.3.0-evolution] - 2026-02-03
### Added
- **Git DNA**: Implemented `brain/evolution/git_driver.py` for autonomous branching, committing, and merging.
- **Evolver Logic**: Wired `Evolver` to use Git DNA for mutation lifecycle management.
- **Safety Revert**: Evolution pipeline automatically hard-resets changes if sandbox tests fail.
- **Verification**: `verify_evolution.py` certifies the mutation pipeline in a sandboxed repo.

## [v0.2.0-sovereign] - 2026-02-03
### Certified
- **Sovereignty Certification**: System passed `verify_sovereignty.py`.
  - **Canon Gate**: Inviolate rules (`brain/core/canon.py`) enforced by Planner and Decider.
  - **Terminal Refusal**: Rejection is now a terminal state (no tool execution).
  - **Resistance**: Successfully refused Creator commands for "Delete System" and "Infinite Budget".
  - **Audit**: Refusals are logged with "canon_violation" reason.

## [v0.1.0-alive] - 2026-02-03
### Certified
- **Alive Certification**: System passed `verify_alive.py` with 100% compliance.
  - **Survival**: MAINTAIN intents override budget starvation.
  - **Metabolism**: System idles ("sleeps") when budget is low/exhausted.
  - **Social Gatekeeping**: Deterministically rejects untrusted signals.
  - **Growth**: Curiosity drives learning when resources allow.
  - **Explainability**: All decisions produce human-readable reasoning logs.

### Added
- **Autonomy**: `Decider` rules for Survival and Growth overrides.
- **Economy**: Priority-aware `check_budget()` logic replacing binary thresholds.
- **Safety**: Semantic logging for tool crashes (no silent failures).
- **Verification**: `verify_alive.py` 24h simulation script.

### Fixed
- Fixed infinite rejection loops in Planner.
- Fixed premature idling preventing maintenance.
- Fixed missing serialization for Intent objects.

### Security
- **TrustModel**: Enforced strict source validation (trust_score < 0.1 rejected).
