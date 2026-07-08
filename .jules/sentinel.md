## 2025-02-06 - Default Insecure Configuration
**Vulnerability:** Hardcoded API key ("ippoc-secret-key") used as default in `src/cortex/cortex/server.py`.
**Learning:** Default configurations for development often make their way into production or expose systems during testing if not explicitly overridden. The system relied on a specific hardcoded string for default auth, which is a Critical vulnerability (CWE-798).
**Prevention:** Never provide a hardcoded default for secrets. If a secret is missing, either generate a secure random one at runtime (fail-safe) or refuse to start (fail-secure).

## 2025-02-06 - Command Injection via child_process.exec
**Vulnerability:** Command injection vulnerabilities in `src/ippoc/cortex/cortex/openclaw-cortex/src/agents/toolsmith.ts` and `thalamus.ts` due to using `child_process.exec` with unsanitized inputs like `name`, `pathStr`, `resourceFlag`, and `signal.payload.pid`.
**Learning:** Using `child_process.exec` passes the entire command string to a shell, making it trivial for an attacker to inject arbitrary commands if any part of the string comes from user input or external signals.
**Prevention:** Always use `child_process.execFile` or `child_process.spawn` with an array of arguments, which avoids invoking a shell and safely passes arguments directly to the executable.
