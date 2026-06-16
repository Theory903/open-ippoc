## 2025-02-06 - Default Insecure Configuration
**Vulnerability:** Hardcoded API key ("ippoc-secret-key") used as default in `src/cortex/cortex/server.py`.
**Learning:** Default configurations for development often make their way into production or expose systems during testing if not explicitly overridden. The system relied on a specific hardcoded string for default auth, which is a Critical vulnerability (CWE-798).
**Prevention:** Never provide a hardcoded default for secrets. If a secret is missing, either generate a secure random one at runtime (fail-safe) or refuse to start (fail-secure).
## 2026-05-24 - [Command Injection via child_process.exec]
**Vulnerability:** Found `child_process.exec` being used to dynamically run shell commands with unsanitized user inputs (`pid`, `name`, `pathStr`).
**Learning:** The use of `exec` is inherently vulnerable to command injection if arguments contain shell metacharacters.
**Prevention:** Always use `child_process.execFile` or `child_process.spawn` with explicitly parsed argument arrays instead of string concatenation for dynamic commands. Ensure to provide an error callback for `execFile`.
