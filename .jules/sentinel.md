## 2025-02-06 - Default Insecure Configuration
**Vulnerability:** Hardcoded API key ("ippoc-secret-key") used as default in `src/cortex/cortex/server.py`.
**Learning:** Default configurations for development often make their way into production or expose systems during testing if not explicitly overridden. The system relied on a specific hardcoded string for default auth, which is a Critical vulnerability (CWE-798).
**Prevention:** Never provide a hardcoded default for secrets. If a secret is missing, either generate a secure random one at runtime (fail-safe) or refuse to start (fail-secure).

## 2026-04-11 - Prevent Command and Signal Injection in TS Event Handlers
**Vulnerability:** Untrusted external properties (`signal.payload.pid`) were passed directly into `process.kill()` and `cp.exec()` via string interpolation, allowing signal and command injection.
**Learning:** Even internal signaling systems (like Thalamus) can be exploited if the payload origin is untrusted or unvalidated. `cp.exec` evaluates full shell syntax, which executes injected commands.
**Prevention:** Always validate and cast untrusted inputs intended for system use (e.g., using `Number.isInteger(Number(pid))`). Use safe execution wrappers like `cp.execFile` or `cp.spawn` that do not evaluate shell syntax instead of `cp.exec`.
