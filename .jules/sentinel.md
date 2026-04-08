## 2025-02-06 - Default Insecure Configuration
**Vulnerability:** Hardcoded API key ("ippoc-secret-key") used as default in `src/cortex/cortex/server.py`.
**Learning:** Default configurations for development often make their way into production or expose systems during testing if not explicitly overridden. The system relied on a specific hardcoded string for default auth, which is a Critical vulnerability (CWE-798).
**Prevention:** Never provide a hardcoded default for secrets. If a secret is missing, either generate a secure random one at runtime (fail-safe) or refuse to start (fail-secure).

## 2025-04-08 - Command Injection in Reflex Rules
**Vulnerability:** Command injection and unsafe process killing via untrusted `signal.payload.pid` in `thalamus.ts`.
**Learning:** Using untrusted inputs directly in `cp.exec` or `process.kill` allows for arbitrary code execution if the payload is malicious.
**Prevention:** Always validate external inputs like PIDs as integers (`Number.isInteger`) and use safe APIs like `cp.execFile` instead of `cp.exec` to avoid shell interpolation.
