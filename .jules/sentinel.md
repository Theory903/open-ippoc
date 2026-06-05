## 2025-02-06 - Default Insecure Configuration
**Vulnerability:** Hardcoded API key ("ippoc-secret-key") used as default in `src/cortex/cortex/server.py`.
**Learning:** Default configurations for development often make their way into production or expose systems during testing if not explicitly overridden. The system relied on a specific hardcoded string for default auth, which is a Critical vulnerability (CWE-798).
**Prevention:** Never provide a hardcoded default for secrets. If a secret is missing, either generate a secure random one at runtime (fail-safe) or refuse to start (fail-secure).
## 2024-05-26 - Command Injection via `renice` in `thalamus.ts`
**Vulnerability:** The Thalamus agent uses `cp.exec("renice +10 -p " + signal.payload.pid)` without verifying that `pid` is an integer, leading to potential command injection if the payload's `pid` field contains unsanitized input.
**Learning:** `child_process.exec` should not be used with dynamic user or system inputs without validation or sanitization.
**Prevention:** Use `child_process.execFile` and pass arguments as an array instead, or ensure dynamic payloads are strictly typed and validated (e.g., verifying `pid` is a number).
