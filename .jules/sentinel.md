## 2025-02-06 - Default Insecure Configuration
**Vulnerability:** Hardcoded API key ("ippoc-secret-key") used as default in `src/cortex/cortex/server.py`.
**Learning:** Default configurations for development often make their way into production or expose systems during testing if not explicitly overridden. The system relied on a specific hardcoded string for default auth, which is a Critical vulnerability (CWE-798).
**Prevention:** Never provide a hardcoded default for secrets. If a secret is missing, either generate a secure random one at runtime (fail-safe) or refuse to start (fail-secure).
## 2024-10-24 - [CRITICAL] Fix Command Injection in Thalamus Reflex
**Vulnerability:** Found `cp.exec(renice +10 -p ${signal.payload.pid})` in `thalamus.ts` which is vulnerable to command injection since `signal.payload.pid` is not validated.
**Learning:** External or kernel-level signals containing unstructured payloads can be injected directly into shell execution streams, leading to arbitrary command execution without input sanitization or explicit parameterization via `execFile`.
**Prevention:** Always use `execFile` with an array of arguments and explicitly parse/validate data types (e.g. `Number(pid)`) when passing user or external data to system subprocesses.
