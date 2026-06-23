## 2025-02-06 - Default Insecure Configuration
**Vulnerability:** Hardcoded API key ("ippoc-secret-key") used as default in `src/cortex/cortex/server.py`.
**Learning:** Default configurations for development often make their way into production or expose systems during testing if not explicitly overridden. The system relied on a specific hardcoded string for default auth, which is a Critical vulnerability (CWE-798).
**Prevention:** Never provide a hardcoded default for secrets. If a secret is missing, either generate a secure random one at runtime (fail-safe) or refuse to start (fail-secure).

## 2025-02-12 - Prevent Command Injection via execFile
**Vulnerability:** Found multiple usages of `child_process.exec` (via `promisify(exec)`) constructed using template literals or string concatenation, presenting a command injection vulnerability.
**Learning:** Using `exec` invokes a shell, making it susceptible to shell metacharacters if user input is interpolated into the command string. `execFile` avoids the shell and passes arguments directly to the executable.
**Prevention:** Always use `execFile` or `spawn` with an array of arguments instead of `exec` when invoking external processes, to ensure arguments are not evaluated by a shell.
