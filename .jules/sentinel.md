## 2025-02-06 - Default Insecure Configuration
**Vulnerability:** Hardcoded API key ("ippoc-secret-key") used as default in `src/cortex/cortex/server.py`.
**Learning:** Default configurations for development often make their way into production or expose systems during testing if not explicitly overridden. The system relied on a specific hardcoded string for default auth, which is a Critical vulnerability (CWE-798).
**Prevention:** Never provide a hardcoded default for secrets. If a secret is missing, either generate a secure random one at runtime (fail-safe) or refuse to start (fail-secure).
## 2024-05-24 - Command Injection via exec
**Vulnerability:** Found `cp.exec(\`renice +10 -p ${signal.payload.pid}\`)` in `thalamus.ts`, which allows command injection if `pid` is not properly sanitized or comes from an untrusted source.
**Learning:** Using `child_process.exec` with string interpolation for system commands is dangerous.
**Prevention:** Always use `child_process.execFile` or `child_process.spawn` with an array of arguments, preventing the shell from interpreting arbitrary characters.
