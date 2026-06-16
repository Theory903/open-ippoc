## 2025-02-06 - Default Insecure Configuration
**Vulnerability:** Hardcoded API key ("ippoc-secret-key") used as default in `src/cortex/cortex/server.py`.
**Learning:** Default configurations for development often make their way into production or expose systems during testing if not explicitly overridden. The system relied on a specific hardcoded string for default auth, which is a Critical vulnerability (CWE-798).
**Prevention:** Never provide a hardcoded default for secrets. If a secret is missing, either generate a secure random one at runtime (fail-safe) or refuse to start (fail-secure).
## 2024-05-24 - Avoid dynamic exec for shell commands
**Vulnerability:** Found `exec` being used to dynamically construct shell commands with unsanitized arguments, leading to potential command injection.
**Learning:** Using `child_process.exec` with dynamic inputs passes the string directly to a shell, making it trivial to inject malicious commands.
**Prevention:** Always use `child_process.execFile` or `child_process.spawn` and pass arguments as an array to ensure the arguments are passed safely without being interpreted by a shell.
