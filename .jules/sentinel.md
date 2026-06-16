## 2025-02-06 - Default Insecure Configuration
**Vulnerability:** Hardcoded API key ("ippoc-secret-key") used as default in `src/cortex/cortex/server.py`.
**Learning:** Default configurations for development often make their way into production or expose systems during testing if not explicitly overridden. The system relied on a specific hardcoded string for default auth, which is a Critical vulnerability (CWE-798).
**Prevention:** Never provide a hardcoded default for secrets. If a secret is missing, either generate a secure random one at runtime (fail-safe) or refuse to start (fail-secure).
## 2024-05-24 - Command Injection via Python Subprocess
**Vulnerability:** Arbitrary code execution vulnerability in `openclaw_tool_integrator.py` where `os.path.join` outputs were injected directly into a Python command executed via `subprocess.run(..., "python3", "-c", ...)` without escaping.
**Learning:** Shelling out to python to run sqlite commands is inefficient and vulnerable when variables are interpolated into the string, especially paths which can contain shell/code metacharacters (e.g. usernames with quotes).
**Prevention:** Avoid shelling out to Python from Python. Use the builtin `sqlite3` library directly within the parent process to maintain type safety and avoid string interpolation attacks.
