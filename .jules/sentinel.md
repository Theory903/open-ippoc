## 2025-02-06 - Default Insecure Configuration
**Vulnerability:** Hardcoded API key ("ippoc-secret-key") used as default in `src/cortex/cortex/server.py`.
**Learning:** Default configurations for development often make their way into production or expose systems during testing if not explicitly overridden. The system relied on a specific hardcoded string for default auth, which is a Critical vulnerability (CWE-798).
**Prevention:** Never provide a hardcoded default for secrets. If a secret is missing, either generate a secure random one at runtime (fail-safe) or refuse to start (fail-secure).
## 2024-05-14 - Fix Command Injection in Thalamus Reflex Agent
**Vulnerability:** A critical command injection vulnerability in `src/cortex/cortex/openclaw-cortex/openclaw-cortex/src/agents/thalamus.ts` where `cp.exec` was used with string interpolation for `signal.payload.pid`.
**Learning:** Event payloads, even internal ones like `signal.payload.pid`, can be manipulated to inject malicious shell commands. String interpolation in `child_process.exec` is inherently unsafe.
**Prevention:** Always use `child_process.execFile` or `child_process.spawn` with explicit argument arrays instead of `child_process.exec` when incorporating dynamic data into shell commands. Ensure proper error handling is implemented for the callback.
