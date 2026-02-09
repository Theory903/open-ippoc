# IPPOC Capability Law (CAP-01)
**STATUS: IMMUTABLE LAW v1.0.0**
*Any change requires a version bump and justification.*

## 1. The Matrix of Sovereign Action
The dynamic granting and strict enforcement of side-effects within the IPPOC Platform.

## 1. The Principle of Least Permission

All organs and plugins operate in a "Total Restriction" state by default. They have zero access to the host or external networks unless a signed `CapabilityGrant` is presented.

## 2. Core Capability Matrix

| Capability | Scope | Side-Effect |
| :--- | :--- | :--- |
| `cognition.llm` | `provider:model` | Invoke external LLM APIs (OpenAI, Anthropic, etc.) |
| `hal.network` | `whitelist: [cidr]` | Outbound TCP/UDP egress outside the IPPOC mesh |
| `hal.filesystem` | `path: /sub/dir` | Read/Write access outside the instance instance data root |
| `hal.device` | `type: audio|bt` | Direct interaction with hardware drivers |
| `sovereign.vault` | `scope: [api-key]` | Retrieval of stored secrets from Soma |

## 3. Enforcement Points

- **LLM Gateway (Cortex)**: Intercepts all model requests. Checks against `cognition.llm`.
- **Identity Proxy (Soma)**: Intercepts all token requests. Checks against `sovereign.vault`.
- **Sandbox Manager (HAL)**: Re-wraps all file/network syscalls in the container/sandbox. Checks against `hal.*`.

## 4. Grant Lifecycle

1. **Declaration**: A plugin/organ declares its required capabilities in `manifest.json`.
2. **Approval**: The Instance Owner grants these during `ippoc setup`.
3. **Issuance**: Soma issues a JWT-signed `CapabilityGrant`.
4. **Verification**: The Enforcement Point verifies the signature and scope on EVERY call.

## 5. Violation Penalties

- **First Violation**: Immediate Halt of the operation + Critical Warning.
- **Second Violation**: Temporary Isolation of the offending organ (Isolation Mode).
- **Security Breach**: Revocation of all keys + Instance Lockdown.
