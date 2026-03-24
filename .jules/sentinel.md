## 2025-02-06 - Default Insecure Configuration
**Vulnerability:** Hardcoded API key ("ippoc-secret-key") used as default in `src/cortex/cortex/server.py`.
**Learning:** Default configurations for development often make their way into production or expose systems during testing if not explicitly overridden. The system relied on a specific hardcoded string for default auth, which is a Critical vulnerability (CWE-798).
**Prevention:** Never provide a hardcoded default for secrets. If a secret is missing, either generate a secure random one at runtime (fail-safe) or refuse to start (fail-secure).

## 2025-03-24 - Command Injection Vulnerability in Process Throttling
**Vulnerability:** Command injection vulnerability in `Thalamus.ts` when throttling high CPU processes via `cp.exec(renice +10 -p ${signal.payload.pid})`. Untrusted external payload (PID) was concatenated directly into the shell command string without validation.
**Learning:** `cp.exec` evaluates strings inside a shell, allowing attackers to append malicious commands if inputs aren't strictly validated or escaped. Because Node's `child_process` inherits permissions from the running node process, command execution is dangerous if not sanitized.
**Prevention:** Always validate inputs using specific types (e.g., `Number.isInteger(pid)`) and prefer `cp.execFile` or `cp.spawn` to bypass shell evaluation completely by passing arguments as an array.
