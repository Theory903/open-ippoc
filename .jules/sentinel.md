## 2025-02-06 - Default Insecure Configuration
**Vulnerability:** Hardcoded API key ("ippoc-secret-key") used as default in `src/cortex/cortex/server.py`.
**Learning:** Default configurations for development often make their way into production or expose systems during testing if not explicitly overridden. The system relied on a specific hardcoded string for default auth, which is a Critical vulnerability (CWE-798).
**Prevention:** Never provide a hardcoded default for secrets. If a secret is missing, either generate a secure random one at runtime (fail-safe) or refuse to start (fail-secure).
## 2025-05-11 - Command Injection in Agent Processes
**Vulnerability:** child_process.exec was used with dynamic template string interpolation in thalamus.ts and toolsmith.ts, allowing potential command injection risks.
**Learning:** Using `exec` directly instead of `execFile` exposes shell vulnerabilities. When interpolating process arguments, always use `execFile` with an arguments array, and validate numeric inputs for PID management explicitly.
**Prevention:** Always use `child_process.execFile` or `spawn` instead of `exec` to avoid shell execution evaluation, and provide error callbacks.
