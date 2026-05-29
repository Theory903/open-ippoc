## 2025-02-06 - Default Insecure Configuration
**Vulnerability:** Hardcoded API key ("ippoc-secret-key") used as default in `src/cortex/cortex/server.py`.
**Learning:** Default configurations for development often make their way into production or expose systems during testing if not explicitly overridden. The system relied on a specific hardcoded string for default auth, which is a Critical vulnerability (CWE-798).
**Prevention:** Never provide a hardcoded default for secrets. If a secret is missing, either generate a secure random one at runtime (fail-safe) or refuse to start (fail-secure).
## 2026-05-29 - [Command Injection via exec]
**Vulnerability:** Found `child_process.exec` constructing shell commands with unsanitized inputs (`name`, `pathStr`, `resourceFlag`).
**Learning:** String interpolation in `exec` enables command injection if inputs contain shell metacharacters.
**Prevention:** Always use `child_process.execFile` or `spawn` with an argument array instead of `exec`.
