# Changelog

All notable changes to the IPPOC project will be documented in this file.

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
