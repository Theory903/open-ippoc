## 2025-02-06 - Default Insecure Configuration
**Vulnerability:** Hardcoded API key ("ippoc-secret-key") used as default in `src/cortex/cortex/server.py`.
**Learning:** Default configurations for development often make their way into production or expose systems during testing if not explicitly overridden. The system relied on a specific hardcoded string for default auth, which is a Critical vulnerability (CWE-798).
**Prevention:** Never provide a hardcoded default for secrets. If a secret is missing, either generate a secure random one at runtime (fail-safe) or refuse to start (fail-secure).
## 2025-02-06 - Command Injection via exec
**Vulnerability:** Thalamus agent used `child_process.exec` to run `renice` on a PID dynamically inserted from a signal payload. Since the PID wasn't sanitized, this exposed the system to Command Injection (CWE-77).
**Learning:** Security fixes involving `child_process.exec` mapped to `execFile` or `spawn` must explicitly supply an error callback or proper event handlers, or else uncaught spawn errors can crash the entire Node process. Also, using dynamic template literal arguments directly in `exec` is inherently unsafe.
**Prevention:** Replace `exec` with `execFile` and isolate arguments in an array format (e.g. `execFile("renice", ["+10", "-p", String(pid)], ...)`) instead of concatenating strings. Always bind an error callback to handle failed process spawns securely.
