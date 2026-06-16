## 2025-02-06 - Default Insecure Configuration
**Vulnerability:** Hardcoded API key ("ippoc-secret-key") used as default in `src/cortex/cortex/server.py`.
**Learning:** Default configurations for development often make their way into production or expose systems during testing if not explicitly overridden. The system relied on a specific hardcoded string for default auth, which is a Critical vulnerability (CWE-798).
**Prevention:** Never provide a hardcoded default for secrets. If a secret is missing, either generate a secure random one at runtime (fail-safe) or refuse to start (fail-secure).

## 2025-03-15 - Unrestricted API Key Generation
**Vulnerability:** The `/v1/auth/issue` endpoint in `src/ippoc/soma/server.py` lacked any authentication or authorization checks, allowing anyone (including remote users) to generate valid API keys. This is a Critical vulnerability (CWE-288: Authentication Bypass).
**Learning:** Endpoints meant strictly for internal or local system bootstrap must enforce constraints like local loopback host checks (`127.0.0.1`, `localhost`, etc.) if they lack explicit authentication tokens.
**Prevention:** For bootstrap or CLI-only API key issuance, explicitly restrict the allowed request host (e.g., using `request.client.host` in FastAPI) to local addresses to prevent unauthorized remote token generation.
