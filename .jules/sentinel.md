## 2025-02-06 - Default Insecure Configuration
**Vulnerability:** Hardcoded API key ("ippoc-secret-key") used as default in `src/cortex/cortex/server.py`.
**Learning:** Default configurations for development often make their way into production or expose systems during testing if not explicitly overridden. The system relied on a specific hardcoded string for default auth, which is a Critical vulnerability (CWE-798).
**Prevention:** Never provide a hardcoded default for secrets. If a secret is missing, either generate a secure random one at runtime (fail-safe) or refuse to start (fail-secure).

## 2025-02-06 - Command Injection via child_process.exec
**Vulnerability:** Use of `child_process.exec` with unescaped input from `signal.payload.pid` allowing arbitrary shell command execution.
**Learning:** In Node.js, `child_process.exec` spawns a shell to execute a command, exposing applications to injection if user or external inputs are interpolated into the command string.
**Prevention:** Always use `child_process.execFile` or `child_process.spawn` without `shell: true` and pass arguments as an array so they are safely passed directly to the binary without shell parsing. Additionally, always handle exceptions in `execFile` callbacks since spawn failures crash the process.
