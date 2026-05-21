## 2025-02-06 - Default Insecure Configuration
**Vulnerability:** Hardcoded API key ("ippoc-secret-key") used as default in `src/cortex/cortex/server.py`.
**Learning:** Default configurations for development often make their way into production or expose systems during testing if not explicitly overridden. The system relied on a specific hardcoded string for default auth, which is a Critical vulnerability (CWE-798).
**Prevention:** Never provide a hardcoded default for secrets. If a secret is missing, either generate a secure random one at runtime (fail-safe) or refuse to start (fail-secure).
## 2024-05-21 - Command Injection via `child_process.exec`
**Vulnerability:** Found a command injection vulnerability where `child_process.exec` was used with string interpolation containing an unvalidated payload `cp.exec(\`renice +10 -p ${signal.payload.pid}\`)`.
**Learning:** Using `exec` with untrusted input can easily lead to arbitrary command execution if the input isn't strictly validated or sanitized.
**Prevention:** Always use `child_process.execFile` or `child_process.spawn` with an array of arguments to avoid shell execution and interpolation risks when dealing with dynamic input.
