## 2025-02-06 - Default Insecure Configuration
**Vulnerability:** Hardcoded API key ("ippoc-secret-key") used as default in `src/cortex/cortex/server.py`.
**Learning:** Default configurations for development often make their way into production or expose systems during testing if not explicitly overridden. The system relied on a specific hardcoded string for default auth, which is a Critical vulnerability (CWE-798).
**Prevention:** Never provide a hardcoded default for secrets. If a secret is missing, either generate a secure random one at runtime (fail-safe) or refuse to start (fail-secure).

## 2025-02-15 - Replace exec with execFile to prevent Command Injection vulnerabilities
**Vulnerability:** Instances of child_process.exec and child_process.execAsync were found being used with untrusted, dynamically-constructed string arguments, risking command injection (CWE-78).
**Learning:** exec spawns a full shell which allows bash/shell syntax evaluation such as piping or chaining && if the arguments contain shell metacharacters. If file inputs or other parameters are un-sanitized, attackers can execute arbitrary shell commands.
**Prevention:** Use child_process.execFile instead of exec, as execFile executes the given binary directly without spawning a shell, inherently neutralizing command injection risks via shell syntax. Provide arguments securely as an array (e.g. ['diff', '--conflict=diff3', file]) instead of a single concatenated string.
