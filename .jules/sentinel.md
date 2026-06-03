## 2025-02-06 - Default Insecure Configuration
**Vulnerability:** Hardcoded API key ("ippoc-secret-key") used as default in `src/cortex/cortex/server.py`.
**Learning:** Default configurations for development often make their way into production or expose systems during testing if not explicitly overridden. The system relied on a specific hardcoded string for default auth, which is a Critical vulnerability (CWE-798).
**Prevention:** Never provide a hardcoded default for secrets. If a secret is missing, either generate a secure random one at runtime (fail-safe) or refuse to start (fail-secure).
## 2024-06-03 - [Command Injection in Thalamus Reflex]
**Vulnerability:** Found cp.exec() using unvalidated signal.payload.pid in thalamus.ts reflex rules.
**Learning:** Event payload parameters used in shell commands must always be validated or parameterized to prevent command injection.
**Prevention:** Use cp.execFile instead of cp.exec, and enforce strict type casting (e.g. String()) when interpolating variables into arguments.
