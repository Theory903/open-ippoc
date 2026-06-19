## 2025-02-06 - Default Insecure Configuration
**Vulnerability:** Hardcoded API key ("ippoc-secret-key") used as default in `src/cortex/cortex/server.py`.
**Learning:** Default configurations for development often make their way into production or expose systems during testing if not explicitly overridden. The system relied on a specific hardcoded string for default auth, which is a Critical vulnerability (CWE-798).
**Prevention:** Never provide a hardcoded default for secrets. If a secret is missing, either generate a secure random one at runtime (fail-safe) or refuse to start (fail-secure).

## 2025-06-19 - Command Injection in Process Throttling
**Vulnerability:** Found `cp.exec(\`renice +10 -p ${signal.payload.pid}\`)` in `thalamus.ts` which allowed command injection via an unvalidated `pid` payload.
**Learning:** Using `child_process.exec` with unvalidated user input creates severe command injection vulnerabilities. Replacing it with `child_process.execFile` neutralizes the threat, but an error callback is required to prevent unhandled promise rejections on spawn failures.
**Prevention:** Always use `execFile` or `spawn` with an array of arguments instead of string concatenation in `exec`. Always provide error callbacks for detached executions.
