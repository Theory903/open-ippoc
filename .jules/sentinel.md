## 2025-02-06 - Default Insecure Configuration
**Vulnerability:** Hardcoded API key ("ippoc-secret-key") used as default in `src/cortex/cortex/server.py`.
**Learning:** Default configurations for development often make their way into production or expose systems during testing if not explicitly overridden. The system relied on a specific hardcoded string for default auth, which is a Critical vulnerability (CWE-798).
**Prevention:** Never provide a hardcoded default for secrets. If a secret is missing, either generate a secure random one at runtime (fail-safe) or refuse to start (fail-secure).
## 2025-03-20 - Command Injection in Thalamus Reflex Rule
**Vulnerability:** Untrusted string interpolation (`cp.exec(\`renice +10 -p ${signal.payload.pid}\`)`) allowed arbitrary shell command injection if an attacker crafted a malicious PID payload.
**Learning:** `cp.exec` evaluates strings inside a shell, making it inherently dangerous when dealing with dynamic inputs, even internal ones.
**Prevention:** Always use `cp.execFile` or `cp.spawn` for system calls, which do not invoke a shell. Additionally, strictly validate numeric inputs (e.g., `Number.isInteger(Number(value))`) before using them in execution contexts.
