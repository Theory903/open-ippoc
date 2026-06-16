## 2025-02-06 - Default Insecure Configuration
**Vulnerability:** Hardcoded API key ("ippoc-secret-key") used as default in `src/cortex/cortex/server.py`.
**Learning:** Default configurations for development often make their way into production or expose systems during testing if not explicitly overridden. The system relied on a specific hardcoded string for default auth, which is a Critical vulnerability (CWE-798).
**Prevention:** Never provide a hardcoded default for secrets. If a secret is missing, either generate a secure random one at runtime (fail-safe) or refuse to start (fail-secure).
## 2026-03-25 - [Command Injection via cp.exec in Thalamus]
**Vulnerability:** Found a command injection vulnerability where unsanitized user input (signal.payload.pid) was passed directly into cp.exec(`renice +10 -p ${signal.payload.pid}`).
**Learning:** This existed because of dynamic string construction using template literals with user-provided arguments in child_process.exec without validation.
**Prevention:** Always use safe integer validation such as Number.isInteger() for PIDs, and use cp.execFile or cp.spawn over cp.exec when dynamically assembling commands with variables.
