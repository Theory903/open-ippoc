## 2025-02-06 - Default Insecure Configuration
**Vulnerability:** Hardcoded API key ("ippoc-secret-key") used as default in `src/cortex/cortex/server.py`.
**Learning:** Default configurations for development often make their way into production or expose systems during testing if not explicitly overridden. The system relied on a specific hardcoded string for default auth, which is a Critical vulnerability (CWE-798).
**Prevention:** Never provide a hardcoded default for secrets. If a secret is missing, either generate a secure random one at runtime (fail-safe) or refuse to start (fail-secure).
## 2025-02-06 - Command Injection in ToolSmith
**Vulnerability:** Command injection in `createSkill` method of `ToolSmith` agent (`src/cortex/cortex/openclaw-cortex/openclaw-cortex/src/agents/toolsmith.ts` and mirrored locations). The method used `child_process.exec()` with unsanitized arguments concatenated into a string command, allowing arbitrary command execution if the `name` or `pathStr` variables contained shell metacharacters.
**Learning:** `child_process.exec()` should be avoided when executing external programs with dynamic arguments because it invokes a shell and relies on string formatting, exposing the system to injection vulnerabilities.
**Prevention:** Use `child_process.execFile()` or `child_process.spawn()` which execute the binary directly and pass arguments as an array instead of a single string. This bypasses the shell completely and prevents command injection.
