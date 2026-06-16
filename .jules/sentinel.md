## 2025-02-06 - Default Insecure Configuration
**Vulnerability:** Hardcoded API key ("ippoc-secret-key") used as default in `src/cortex/cortex/server.py`.
**Learning:** Default configurations for development often make their way into production or expose systems during testing if not explicitly overridden. The system relied on a specific hardcoded string for default auth, which is a Critical vulnerability (CWE-798).
**Prevention:** Never provide a hardcoded default for secrets. If a secret is missing, either generate a secure random one at runtime (fail-safe) or refuse to start (fail-secure).

## 2026-05-03 - Command Injection via child_process.exec
**Vulnerability:** Found `cp.exec` executing `renice +10 -p ${signal.payload.pid}` with unsanitized signal payload data in `thalamus.ts`, causing a CRITICAL Command Injection vulnerability.
**Learning:** Dynamic values coming from signals or events can be manipulated and should never be interpolated into shell strings using `cp.exec`.
**Prevention:** Use `cp.execFile` with an argument array instead of a concatenated shell string to prevent shell injection, and ensure to properly handle errors using the callback to prevent uncaught exceptions crashing the process.
