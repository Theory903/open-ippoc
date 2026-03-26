## 2025-02-06 - Default Insecure Configuration
**Vulnerability:** Hardcoded API key ("ippoc-secret-key") used as default in `src/cortex/cortex/server.py`.
**Learning:** Default configurations for development often make their way into production or expose systems during testing if not explicitly overridden. The system relied on a specific hardcoded string for default auth, which is a Critical vulnerability (CWE-798).
**Prevention:** Never provide a hardcoded default for secrets. If a secret is missing, either generate a secure random one at runtime (fail-safe) or refuse to start (fail-secure).

## 2026-03-26 - [Thalamus PID Injection Fix]
**Vulnerability:** Untrusted string input from `signal.payload.pid` was passed directly to Node's `cp.exec()` and `process.kill()`, exposing the system to potential command injection and signal injection.
**Learning:** Even internal system signals or events may carry unsanitized payloads; passing these directly to shell interpreters (`exec`) or system-level APIs (`kill`) allows arbitrary command execution or killing of unintended processes if the PID contains strings like `1234; rm -rf /`.
**Prevention:** Always validate and coerce parameters intended as PIDs or numbers (e.g., using `Number.isInteger(Number(payload.pid))`) before using them in system calls. Furthermore, favor `cp.execFile` or `cp.spawn` over `cp.exec` to avoid relying on a shell interpreter.
