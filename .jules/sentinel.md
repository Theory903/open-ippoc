## 2025-02-06 - Default Insecure Configuration
**Vulnerability:** Hardcoded API key ("ippoc-secret-key") used as default in `src/cortex/cortex/server.py`.
**Learning:** Default configurations for development often make their way into production or expose systems during testing if not explicitly overridden. The system relied on a specific hardcoded string for default auth, which is a Critical vulnerability (CWE-798).
**Prevention:** Never provide a hardcoded default for secrets. If a secret is missing, either generate a secure random one at runtime (fail-safe) or refuse to start (fail-secure).

## 2026-05-01 - Command Injection in ToolSmith
**Vulnerability:** Command Injection in `src/cortex/cortex/openclaw-cortex/openclaw-cortex/src/agents/toolsmith.ts` (and its mirrored instances), where unsanitized user inputs (`name`, `pathStr`) were concatenated directly into a shell command and evaluated using `child_process.exec`.
**Learning:** Tools or scaffolding scripts that construct shell commands from external or user-provided inputs without using array-based argument structures are highly vulnerable to Command Injection on the host OS.
**Prevention:** Never use `child_process.exec` when incorporating dynamic or user-controlled input. Always refactor to use `child_process.execFile` or `child_process.spawn`, where arguments are passed as a distinct, safe array, thereby preventing the shell from interpolating them as executable commands.
