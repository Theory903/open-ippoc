## 2025-02-06 - Default Insecure Configuration
**Vulnerability:** Hardcoded API key ("ippoc-secret-key") used as default in `src/cortex/cortex/server.py`.
**Learning:** Default configurations for development often make their way into production or expose systems during testing if not explicitly overridden. The system relied on a specific hardcoded string for default auth, which is a Critical vulnerability (CWE-798).
**Prevention:** Never provide a hardcoded default for secrets. If a secret is missing, either generate a secure random one at runtime (fail-safe) or refuse to start (fail-secure).
## 2025-06-05 - Command Injection in Thalamus Reflexes
**Vulnerability:** Command Injection in `src/cortex/cortex/openclaw-cortex/openclaw-cortex/src/agents/thalamus.ts` due to unsanitized payload directly interpolated into `child_process.exec`.
**Learning:** Using `cp.exec` with unvalidated input (e.g., `signal.payload.pid`) allows execution of arbitrary shell commands. It is crucial to be careful with any system inputs passed to shell executors.
**Prevention:** Always use `cp.execFile` instead of `cp.exec` to pass arguments as an array rather than a single string, or explicitly validate and sanitize all inputs to ensure they only contain the expected format (e.g., validating that PID is strictly numeric).
