## 2025-02-06 - Default Insecure Configuration
**Vulnerability:** Hardcoded API key ("ippoc-secret-key") used as default in `src/cortex/cortex/server.py`.
**Learning:** Default configurations for development often make their way into production or expose systems during testing if not explicitly overridden. The system relied on a specific hardcoded string for default auth, which is a Critical vulnerability (CWE-798).
**Prevention:** Never provide a hardcoded default for secrets. If a secret is missing, either generate a secure random one at runtime (fail-safe) or refuse to start (fail-secure).
## 2024-06-25 - [Command Injection in Thalamus Reflex Action]
**Vulnerability:** Unsanitized `signal.payload.pid` was concatenated directly into a `cp.exec` call for `renice` in `thalamus.ts`.
**Learning:** Even internal event payloads like `pid` must be treated as untrusted input. `child_process.exec` passes strings to a shell, allowing arbitrary command injection if the payload contains characters like `;` or `&&`.
**Prevention:** Always use `child_process.execFile` or `spawn` with parameterized arguments instead of `exec` with string concatenation. Additionally, when refactoring to `execFile`, always provide an error callback to avoid unhandled spawn errors crashing the process.
