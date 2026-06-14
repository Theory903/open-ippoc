## 2025-02-06 - Default Insecure Configuration
**Vulnerability:** Hardcoded API key ("ippoc-secret-key") used as default in `src/cortex/cortex/server.py`.
**Learning:** Default configurations for development often make their way into production or expose systems during testing if not explicitly overridden. The system relied on a specific hardcoded string for default auth, which is a Critical vulnerability (CWE-798).
**Prevention:** Never provide a hardcoded default for secrets. If a secret is missing, either generate a secure random one at runtime (fail-safe) or refuse to start (fail-secure).

## 2025-02-06 - Unsanitized PID Command Injection in Thalamus Reflex
**Vulnerability:** Command injection vulnerability in the Thalamus agent's HIGH_CPU_USAGE reflex handler (`cp.exec(\`renice +10 -p ${signal.payload.pid}\`)`). A malicious `signal.payload.pid` (e.g., `123; rm -rf /`) could execute arbitrary commands. A similar issue existed for `process.kill()` expecting an unvalidated string which could cause crashes or unexpected behaviors.
**Learning:** `child_process.exec` passes the entire command string to a shell, making it inherently vulnerable to command injection when interpolating untrusted input. Type definitions (`any` payload) further disguised the missing validation.
**Prevention:** Always use `child_process.execFile` or `spawn` with an array of arguments to bypass shell interpretation. Additionally, strictly parse and validate integer fields (like PIDs) using `parseInt` or similar type-casting techniques before utilizing them in system calls.
