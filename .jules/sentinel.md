## 2025-02-06 - Default Insecure Configuration
**Vulnerability:** Hardcoded API key ("ippoc-secret-key") used as default in `src/cortex/cortex/server.py`.
**Learning:** Default configurations for development often make their way into production or expose systems during testing if not explicitly overridden. The system relied on a specific hardcoded string for default auth, which is a Critical vulnerability (CWE-798).
**Prevention:** Never provide a hardcoded default for secrets. If a secret is missing, either generate a secure random one at runtime (fail-safe) or refuse to start (fail-secure).

## 2024-06-25 - Prevent command injection by avoiding `child_process.exec`
**Vulnerability:** Command injection vulnerability in `ToolSmith.createSkill` due to using string concatenation with `child_process.exec`, exposing the agent to executing arbitrary code if parameters contain shell metacharacters. `Thalamus.initializeReflexRules` also used `exec` unsafely with the PID parameter without error handling callbacks.
**Learning:** Using `exec` over `execFile` or `spawn` allows shell expansion which makes it easy to introduce command injections. Further, Node.js `execFile` without a callback can cause unhandled exceptions.
**Prevention:** Always use `execFile` or `spawn` and pass parameters as an array instead of concatenating strings. Also, ensure a callback is provided when using the callback-based signature of `execFile`.
