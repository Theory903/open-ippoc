## 2025-02-06 - Default Insecure Configuration
**Vulnerability:** Hardcoded API key ("ippoc-secret-key") used as default in `src/cortex/cortex/server.py`.
**Learning:** Default configurations for development often make their way into production or expose systems during testing if not explicitly overridden. The system relied on a specific hardcoded string for default auth, which is a Critical vulnerability (CWE-798).
**Prevention:** Never provide a hardcoded default for secrets. If a secret is missing, either generate a secure random one at runtime (fail-safe) or refuse to start (fail-secure).
## 2026-05-12 - Command Injection in Thalamus Reflex Rules
**Vulnerability:** The `HIGH_CPU_USAGE` reflex rule in `thalamus.ts` used `cp.exec` with an untrusted parameter (`signal.payload.pid`) directly interpolated into the command string.
**Learning:** Kernel and system events passed through the OpenClaw Cortex agent framework (like Thalamus) can contain malicious or malformed payloads. Direct string interpolation in `exec` creates a critical command injection vector.
**Prevention:** Always use `child_process.execFile` or `spawn` instead of `exec`, passing dynamic arguments as an explicit array rather than a formatted string. Ensure error callbacks are provided to handle spawn failures.
