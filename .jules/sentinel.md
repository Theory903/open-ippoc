## 2025-02-06 - Default Insecure Configuration
**Vulnerability:** Hardcoded API key ("ippoc-secret-key") used as default in `src/cortex/cortex/server.py`.
**Learning:** Default configurations for development often make their way into production or expose systems during testing if not explicitly overridden. The system relied on a specific hardcoded string for default auth, which is a Critical vulnerability (CWE-798).
**Prevention:** Never provide a hardcoded default for secrets. If a secret is missing, either generate a secure random one at runtime (fail-safe) or refuse to start (fail-secure).
## 2025-02-06 - Command Injection via child_process.exec in ToolSmith
**Vulnerability:** Use of `child_process.exec` in `toolsmith.ts` and `toolsmith.js` for executing the skill creator script with unsanitized inputs (`name`, `pathStr`, `resources`), allowing potential command injection (CWE-78).
**Learning:** `child_process.exec` executes commands within a shell environment, which interprets metacharacters (e.g., `;`, `&`, `|`). Passing user-supplied or externally-sourced strings directly into the command string can allow arbitrary command execution.
**Prevention:** Always use `child_process.execFile` or `child_process.spawn` with an array of arguments to execute commands directly without a shell, avoiding shell injection risks.
