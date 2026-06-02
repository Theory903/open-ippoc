## 2025-02-06 - Default Insecure Configuration
**Vulnerability:** Hardcoded API key ("ippoc-secret-key") used as default in `src/cortex/cortex/server.py`.
**Learning:** Default configurations for development often make their way into production or expose systems during testing if not explicitly overridden. The system relied on a specific hardcoded string for default auth, which is a Critical vulnerability (CWE-798).
**Prevention:** Never provide a hardcoded default for secrets. If a secret is missing, either generate a secure random one at runtime (fail-safe) or refuse to start (fail-secure).
## 2025-05-24 - [Command Injection]
**Vulnerability:** child_process.exec() was used to run `renice` with an unsanitized `signal.payload.pid`, enabling command injection.
**Learning:** Using exec() with dynamic inputs in Node.js applications creates shell injection vulnerabilities even with seemingly safe numerical IDs like PIDs.
**Prevention:** Always use `execFile` or `spawn` passing dynamic inputs as discrete elements in an arguments array, rather than embedding them in a string.
