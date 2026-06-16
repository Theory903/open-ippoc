## 2025-02-06 - Default Insecure Configuration
**Vulnerability:** Hardcoded API key ("ippoc-secret-key") used as default in `src/cortex/cortex/server.py`.
**Learning:** Default configurations for development often make their way into production or expose systems during testing if not explicitly overridden. The system relied on a specific hardcoded string for default auth, which is a Critical vulnerability (CWE-798).
**Prevention:** Never provide a hardcoded default for secrets. If a secret is missing, either generate a secure random one at runtime (fail-safe) or refuse to start (fail-secure).

## 2025-02-06 - Command Injection via Dynamic Execution
**Vulnerability:** Command injection vulnerability (CWE-78) due to `cp.exec` combined with a dynamically constructed string (`cp.exec(\`renice +10 -p ${signal.payload.pid}\`)`) in `src/agents/thalamus.ts`.
**Learning:** `child_process.exec` passes the command string to a shell, making it susceptible to command injection if any part of the string is derived from untrusted input (e.g., `signal.payload.pid`).
**Prevention:** Always use `child_process.execFile` or `child_process.spawn` instead of `exec`, as these APIs execute binaries directly without spawning a shell, passing arguments as a safe array instead of a parsed string.
