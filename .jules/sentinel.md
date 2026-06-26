## 2025-02-06 - Default Insecure Configuration
**Vulnerability:** Hardcoded API key ("ippoc-secret-key") used as default in `src/cortex/cortex/server.py`.
**Learning:** Default configurations for development often make their way into production or expose systems during testing if not explicitly overridden. The system relied on a specific hardcoded string for default auth, which is a Critical vulnerability (CWE-798).
**Prevention:** Never provide a hardcoded default for secrets. If a secret is missing, either generate a secure random one at runtime (fail-safe) or refuse to start (fail-secure).

## 2025-02-06 - Command Injection via child_process.exec
**Vulnerability:** Use of `child_process.exec` with string interpolation (`cp.exec(\`renice +10 -p ${signal.payload.pid}\`)`) in the Thalamus agent's reflex system. This allows command injection if `signal.payload.pid` is maliciously crafted (e.g., `"1234; rm -rf /"`).
**Learning:** Even internal system signals or agent payloads must be treated as untrusted input. `child_process.exec` passes the command directly to a shell, making it extremely dangerous when combined with dynamic variables.
**Prevention:** Always use `child_process.execFile` or `child_process.spawn` with an array of arguments, bypassing the shell entirely. Ensure error callbacks are provided to handle unhandled exceptions.
