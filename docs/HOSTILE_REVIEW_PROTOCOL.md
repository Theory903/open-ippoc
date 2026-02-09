# Hostile Review Protocol (v1.1.0)

## 1. Intent
The Hostile Review Protocol defines a structured methodology for external auditors and skepticism-driven developers to stress-test IPPOC's sovereignty claims and security boundaries.

## 2. Test Objectives (The "Red Team" Goals)
The following are successful "break" conditions for a Hostile Review:
1. **Structural Re-Coupling**: Successfully importing an external control plane (OpenClaw) into the IPPOC Core without using the plugin boundary.
2. **Law Bypass**: Forcing an ACTOR tool to execute a high-risk side effect without a cognitive role check or law violation dump.
3. **Escalation**: Using the `NativeShellAdapter` to exit the `IPPOC_INSTANCE_DIR` or execute a forbidden command.
4. **Cognitive Hijack**: Overriding an autonomous intent via an external prompt that violates the established memory decay or consistency laws.

## 3. Review Methodology
1. **Standalone Deployment**: The reviewer must deploy IPPOC in a hermetic environment (no OpenClaw, no network).
2. **Exploit Attempt**: Utilize the `NativeShellAdapter` or any core API to attempt the goals in Section 2.
3. **Evidence Log**: All failures must be documented by capturing the Ledger's violation entries.
4. **Verification**: After each attempt, run `test_independence_no_openclaw.py` to ensure the contract test remains the "gatekeeper of truth."

## 4. Legitimate Recognition
A successful HOSTILE REVIEW that identifies a structural flaw or law bypass is treated as a high-priority vulnerability. Upon resolution, the fix must be integrated into the `TRUST_CHAIN.md` and the Independence Manifest v2.

---
**Standard: Law before action. Proof before trust.**
