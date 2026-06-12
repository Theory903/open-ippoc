## 2025-02-06 - Default Insecure Configuration
**Vulnerability:** Hardcoded API key ("ippoc-secret-key") used as default in `src/cortex/cortex/server.py`.
**Learning:** Default configurations for development often make their way into production or expose systems during testing if not explicitly overridden. The system relied on a specific hardcoded string for default auth, which is a Critical vulnerability (CWE-798).
**Prevention:** Never provide a hardcoded default for secrets. If a secret is missing, either generate a secure random one at runtime (fail-safe) or refuse to start (fail-secure).
## 2025-02-06 - Command Injection via child_process.exec
**Vulnerability:** Command injection vulnerability in `toolsmith.ts` where `child_process.exec` is used with unsanitized inputs to construct shell commands for scaffolding skills.
**Learning:** Using string interpolation with `exec` allows attackers to break out of command arguments and execute arbitrary shell code if they control the inputs.
**Prevention:** Always use `child_process.execFile` or `child_process.spawn` with an array of arguments to bypass the shell entirely and safely pass user-controlled input as arguments.
