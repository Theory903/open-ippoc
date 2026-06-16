## 2025-02-06 - Default Insecure Configuration
**Vulnerability:** Hardcoded API key ("ippoc-secret-key") used as default in `src/cortex/cortex/server.py`.
**Learning:** Default configurations for development often make their way into production or expose systems during testing if not explicitly overridden. The system relied on a specific hardcoded string for default auth, which is a Critical vulnerability (CWE-798).
**Prevention:** Never provide a hardcoded default for secrets. If a secret is missing, either generate a secure random one at runtime (fail-safe) or refuse to start (fail-secure).
## 2026-03-13 - Command Injection via Python String Interpolation
**Vulnerability:** Command injection vulnerability in `_integrate_telegram` due to string interpolation of path names in dynamically generated python script running via `subprocess.run`.
**Learning:** Path names containing special characters (like single quotes) can cause syntax errors or allow arbitrary code execution when interpolated into stringified python scripts.
**Prevention:** Always pass variables to subprocess scripts via command-line arguments (e.g., `sys.argv`) or environment variables, instead of string interpolation.
