## 2025-02-06 - Default Insecure Configuration
**Vulnerability:** Hardcoded API key ("ippoc-secret-key") used as default in `src/cortex/cortex/server.py`.
**Learning:** Default configurations for development often make their way into production or expose systems during testing if not explicitly overridden. The system relied on a specific hardcoded string for default auth, which is a Critical vulnerability (CWE-798).
**Prevention:** Never provide a hardcoded default for secrets. If a secret is missing, either generate a secure random one at runtime (fail-safe) or refuse to start (fail-secure).

## 2026-04-10 - Prevent Command and Signal Injection in Thalamus Reflexes
**Vulnerability:** Untrusted inputs (`signal.payload.pid`) were passed directly to `process.kill` and `child_process.exec`, enabling signal injection and arbitrary command execution.
**Learning:** System reflexes handling external signals must validate and sanitize all inputs, even for administrative tasks like killing or renicing processes. `child_process.exec` should never be used with dynamic strings.
**Prevention:** Always validate numeric inputs (e.g., `Number.isInteger`) before passing them to OS-level APIs. Use `child_process.execFile` or `spawn` instead of `exec` to safely pass arguments without shell evaluation.
