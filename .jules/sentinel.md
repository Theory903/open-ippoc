## 2025-02-06 - Default Insecure Configuration
**Vulnerability:** Hardcoded API key ("ippoc-secret-key") used as default in `src/cortex/cortex/server.py`.
**Learning:** Default configurations for development often make their way into production or expose systems during testing if not explicitly overridden. The system relied on a specific hardcoded string for default auth, which is a Critical vulnerability (CWE-798).
**Prevention:** Never provide a hardcoded default for secrets. If a secret is missing, either generate a secure random one at runtime (fail-safe) or refuse to start (fail-secure).

## 2025-02-06 - Sensitive Data Exposure in Auth Verify Endpoint
**Vulnerability:** The `/v1/auth/verify` endpoint in Soma accepted API keys via query parameters (`?api_key=...`), leading to potential leakage in server logs, proxy logs, and browser history.
**Learning:** Verification endpoints designed for internal service-to-service communication might be used insecurely if they mirror the data they verify in the URL. Even "internal" endpoints should enforce secure transport of secrets (headers/body).
**Prevention:** Use `Authorization` headers (e.g., Bearer) for transmitting secrets. Avoid passing sensitive data in URL parameters for any endpoint, regardless of its intended consumer.
