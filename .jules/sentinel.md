## 2025-02-06 - Default Insecure Configuration
**Vulnerability:** Hardcoded API key ("ippoc-secret-key") used as default in `src/cortex/cortex/server.py`.
**Learning:** Default configurations for development often make their way into production or expose systems during testing if not explicitly overridden. The system relied on a specific hardcoded string for default auth, which is a Critical vulnerability (CWE-798).
**Prevention:** Never provide a hardcoded default for secrets. If a secret is missing, either generate a secure random one at runtime (fail-safe) or refuse to start (fail-secure).

## 2024-05-05 - Fix child_process.exec injection in Thalamus and ToolSmith
**Vulnerability:** child_process.exec() was used to execute shell commands with unvalidated parameters (e.g. signal.payload.pid). This allows an attacker to inject arbitrary shell commands.
**Learning:** Node.js child_process.exec spawns a shell and blindly executes the command string, making any variable interpolations extremely dangerous.
**Prevention:** Use child_process.execFile() or spawn() which pass parameters directly to the binary as an array, completely bypassing shell evaluation.
