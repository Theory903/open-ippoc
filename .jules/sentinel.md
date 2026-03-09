## 2025-02-06 - Default Insecure Configuration
**Vulnerability:** Hardcoded API key ("ippoc-secret-key") used as default in `src/cortex/cortex/server.py`.
**Learning:** Default configurations for development often make their way into production or expose systems during testing if not explicitly overridden. The system relied on a specific hardcoded string for default auth, which is a Critical vulnerability (CWE-798).
**Prevention:** Never provide a hardcoded default for secrets. If a secret is missing, either generate a secure random one at runtime (fail-safe) or refuse to start (fail-secure).
## 2025-03-09 - [Command Injection in Thalamus Reflexes]
**Vulnerability:** Found a CRITICAL command injection vulnerability in `thalamus.ts` and `thalamus.js` where `signal.payload.pid` was being passed directly into `cp.exec(renice +10 -p ${signal.payload.pid});` without validation.
**Learning:** External or indirect signals processing process IDs can easily carry unsanitized input causing catastrophic shell evaluation vulnerabilities. Using template literals with `cp.exec` is inherently risky when interpolating untrusted parameters.
**Prevention:** Always validate parameters representing system IDs (e.g. `Number.isInteger(pid)`) before making system calls. Additionally, always favor `cp.execFile` over `cp.exec` and pass arguments as an explicit array to prevent unintended shell symbol evaluation.
