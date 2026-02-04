# SYSTEM CANON
**Derived from:** `docs/prds/MASTER_CONSTITUTION.md`

This file defines the **technical non-negotiables** for code mutations within the [IPPOC Integrated Flow](./IPPOC_INTEGRATED_FLOW.md) architecture.
Violations of these rules will cause the Evolution Layer to reject a patch.

## Governance Context
These rules ensure the integrity of the brain-powered system where:
- **OpenClaw plugins** safely integrate with IPPOC Brain
- **HAL components** maintain secure, reliable operation
- **Evolution systems** can safely modify code without breaking core functionality
- **Multi-organ coordination** remains stable and predictable

## Forbidden Patterns (HIGH SEVERITY)
*   `eval(`: No dynamic code execution allowed. Prevents security vulnerabilities in the cognitive processing pipeline.
*   `: any`: No implicit any types. Use `unknown` or specific types. Ensures type safety across brain-tool interfaces.
*   `/Users/`: No hardcoded absolute user paths. Use `env` or relative paths. Maintains portability across the distributed system.

## Required Patterns (MEDIUM SEVERITY)
*   **TypeScript Files**: Must include error handling (`try {`) for I/O operations. Critical for brain-orchestrator communication reliability.
*   **HAL Components**: Must import from appropriate sibling modules (e.g., `capability-tokens`). Ensures proper security boundary enforcement.
*   **Brain Integration**: All cognitive components must include fallback mechanisms. Supports the resilient architecture described in [IPPOC Integrated Flow](./IPPOC_INTEGRATED_FLOW.md).
*   **Tool Envelopes**: Must specify `domain`, `action`, and `risk_level`. Required for proper brain organ routing and resource management.
