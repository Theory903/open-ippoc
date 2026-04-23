## 2025-02-06 - Default Insecure Configuration
**Vulnerability:** Hardcoded API key ("ippoc-secret-key") used as default in `src/cortex/cortex/server.py`.
**Learning:** Default configurations for development often make their way into production or expose systems during testing if not explicitly overridden. The system relied on a specific hardcoded string for default auth, which is a Critical vulnerability (CWE-798).
**Prevention:** Never provide a hardcoded default for secrets. If a secret is missing, either generate a secure random one at runtime (fail-safe) or refuse to start (fail-secure).
## 2024-05-24 - [Command Injection via exec in openclaw-cortex agents]
**Vulnerability:** Arbitrary command injection was possible in `toolsmith.ts` because unsanitized parameters (`name`, `pathStr`, and `resources`) were concatenated directly into a `python3` command string passed to `child_process.exec`.
**Learning:** `child_process.exec` uses a shell interpreter by default. When wrapping legacy scripts (like `init_skill.py`) that accept arbitrary arguments, developers often concatenate those arguments manually into command strings, introducing shell injection vulnerabilities.
**Prevention:** Avoid `child_process.exec` when passing any user or external input. Use `child_process.execFile` or `spawn` with arguments passed strictly as an array of strings. `execFile` invokes the binary directly without spawning a shell, guaranteeing arguments are safely handled.
