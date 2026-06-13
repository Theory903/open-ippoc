## 2025-02-06 - Default Insecure Configuration
**Vulnerability:** Hardcoded API key ("ippoc-secret-key") used as default in `src/cortex/cortex/server.py`.
**Learning:** Default configurations for development often make their way into production or expose systems during testing if not explicitly overridden. The system relied on a specific hardcoded string for default auth, which is a Critical vulnerability (CWE-798).
**Prevention:** Never provide a hardcoded default for secrets. If a secret is missing, either generate a secure random one at runtime (fail-safe) or refuse to start (fail-secure).
## 2026-06-13 - [Command Injection in process renice]
**Vulnerability:** Found `child_process.exec` being used to invoke `renice` using unvalidated process IDs from an event payload (`signal.payload.pid`).
**Learning:** This exposes the application to command injection if `signal.payload.pid` is maliciously formed. The asynchronous context of Thalamus agents handling system-level priority events requires strict parameterization.
**Prevention:** Always utilize `child_process.execFile` instead of `child_process.exec` when invoking shell commands with external arguments in Node.js applications to strictly separate the command from its arguments.
