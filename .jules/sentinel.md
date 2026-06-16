## 2025-02-06 - Default Insecure Configuration
**Vulnerability:** Hardcoded API key ("ippoc-secret-key") used as default in `src/cortex/cortex/server.py`.
**Learning:** Default configurations for development often make their way into production or expose systems during testing if not explicitly overridden. The system relied on a specific hardcoded string for default auth, which is a Critical vulnerability (CWE-798).
**Prevention:** Never provide a hardcoded default for secrets. If a secret is missing, either generate a secure random one at runtime (fail-safe) or refuse to start (fail-secure).

## 2025-02-06 - Command Injection in Node.js Process Throttling
**Vulnerability:** Command injection via unsanitized input (`signal.payload.pid`) passed directly to `cp.exec` in `thalamus.ts` and `thalamus.js` process throttling logic.
**Learning:** Using `child_process.exec` with untrusted dynamic input allows arbitrary command execution. Any value injected into the template string can break out of the intended command context.
**Prevention:** Always use `child_process.execFile` or `child_process.spawn` instead of `exec` to pass arguments safely. Alternatively, strictly validate and sanitize inputs (e.g., verifying a PID is a valid integer) before passing them to OS commands.
