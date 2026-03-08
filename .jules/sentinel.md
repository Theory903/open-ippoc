## 2025-02-06 - Default Insecure Configuration
**Vulnerability:** Hardcoded API key ("ippoc-secret-key") used as default in `src/cortex/cortex/server.py`.
**Learning:** Default configurations for development often make their way into production or expose systems during testing if not explicitly overridden. The system relied on a specific hardcoded string for default auth, which is a Critical vulnerability (CWE-798).
**Prevention:** Never provide a hardcoded default for secrets. If a secret is missing, either generate a secure random one at runtime (fail-safe) or refuse to start (fail-secure).
## 2024-05-24 - API Key Issuance Restricted to Local Loopback
**Vulnerability:** The `/v1/auth/issue` endpoint in `src/ippoc/soma/server.py` allowed anyone who could reach the service to generate a new valid API key and bypass authentication checks.
**Learning:** Development-focused endpoints for bootstrapping trust and identities can become critical attack vectors if exposed without local interface restrictions.
**Prevention:** Always restrict security bootstrap or key generation endpoints to the local loopback (`127.0.0.1`, `localhost`, etc.) using FastAPI's `request.client.host` validation.
