## 2025-02-06 - Default Insecure Configuration
**Vulnerability:** Hardcoded API key ("ippoc-secret-key") used as default in `src/cortex/cortex/server.py`.
**Learning:** Default configurations for development often make their way into production or expose systems during testing if not explicitly overridden. The system relied on a specific hardcoded string for default auth, which is a Critical vulnerability (CWE-798).
**Prevention:** Never provide a hardcoded default for secrets. If a secret is missing, either generate a secure random one at runtime (fail-safe) or refuse to start (fail-secure).

## 2025-02-21 - Shell Command Execution (Command Injection Risk)
**Vulnerability:** Use of `child_process.exec` allowing shell execution for unvalidated paths/commands in `conflict-mediator.ts` and `thermal-monitor.ts`.
**Learning:** Functions executing shell commands via `exec` allow attackers to inject malicious shell code if inputs (like filenames or config parameters) are unvalidated, which is a Critical vulnerability (CWE-78).
**Prevention:** Use `child_process.execFile` instead of `exec`, as `execFile` does not spawn a shell and prevents shell metacharacter expansion and injection.
