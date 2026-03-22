## 2025-02-06 - Default Insecure Configuration
**Vulnerability:** Hardcoded API key ("ippoc-secret-key") used as default in `src/cortex/cortex/server.py`.
**Learning:** Default configurations for development often make their way into production or expose systems during testing if not explicitly overridden. The system relied on a specific hardcoded string for default auth, which is a Critical vulnerability (CWE-798).
**Prevention:** Never provide a hardcoded default for secrets. If a secret is missing, either generate a secure random one at runtime (fail-safe) or refuse to start (fail-secure).

## 2024-05-24 - Fix command injection vulnerability in Thalamus agent
**Vulnerability:** A command injection vulnerability in `Thalamus` agent (`thalamus.ts`), which allowed an attacker to execute arbitrary shell commands by crafting a malicious payload with a crafted `pid`.
**Learning:** `cp.exec` evaluates strings via a shell, and directly injecting unsanitized user inputs into the command string allows an attacker to break out of the intended command context by appending their own commands (e.g. `pid=123; rm -rf /`).
**Prevention:** Always use `cp.execFile` or `cp.spawn` for system commands and pass arguments as an array rather than interpolating strings. Always validate and cast untrusted inputs before using them (e.g., check `Number.isInteger(pid)`).
