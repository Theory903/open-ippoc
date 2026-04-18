## 2025-02-06 - Default Insecure Configuration
**Vulnerability:** Hardcoded API key ("ippoc-secret-key") used as default in `src/cortex/cortex/server.py`.
**Learning:** Default configurations for development often make their way into production or expose systems during testing if not explicitly overridden. The system relied on a specific hardcoded string for default auth, which is a Critical vulnerability (CWE-798).
**Prevention:** Never provide a hardcoded default for secrets. If a secret is missing, either generate a secure random one at runtime (fail-safe) or refuse to start (fail-secure).
## 2024-05-24 - Command Injection in Thalamus Reflex Rules
**Vulnerability:** Thalamus agent reflex rules used `child_process.exec` to run `renice` commands, interpolating `signal.payload.pid` directly into the string without sanitization. This allowed command injection if an attacker could construct a KERNEL_EVENT signal with a malicious pid payload.
**Learning:** Even internal signals handling auto-remediation (like throttling processes) can be vulnerable to command injection if the payload data originates from external or untrusted sources (e.g. indirectly via user intent).
**Prevention:** Always use `child_process.execFile` instead of `exec` with an array of arguments, and properly validate/sanitize variables like PIDs (e.g., using `parseInt`) before passing them to OS commands.
