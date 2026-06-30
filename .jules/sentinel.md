## 2025-02-06 - Default Insecure Configuration
**Vulnerability:** Hardcoded API key ("ippoc-secret-key") used as default in `src/cortex/cortex/server.py`.
**Learning:** Default configurations for development often make their way into production or expose systems during testing if not explicitly overridden. The system relied on a specific hardcoded string for default auth, which is a Critical vulnerability (CWE-798).
**Prevention:** Never provide a hardcoded default for secrets. If a secret is missing, either generate a secure random one at runtime (fail-safe) or refuse to start (fail-secure).
## 2025-02-06 - Unsanitized Payload in child_process.exec
**Vulnerability:** Command injection vulnerability in `thalamus.ts` due to `cp.exec(renice +10 -p ${signal.payload.pid})`.
**Learning:** Using `child_process.exec` with string interpolation of external payloads (even structural fields like `pid`) is a critical risk, as malicious payloads can execute arbitrary commands.
**Prevention:** Always use `child_process.execFile` or `spawn` with explicitly separated command and argument arrays. Ensure error callbacks are provided to prevent unhandled rejections.
