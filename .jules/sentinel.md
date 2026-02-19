## 2025-02-06 - Default Insecure Configuration
**Vulnerability:** Hardcoded API key ("ippoc-secret-key") used as default in `src/cortex/cortex/server.py`.
**Learning:** Default configurations for development often make their way into production or expose systems during testing if not explicitly overridden. The system relied on a specific hardcoded string for default auth, which is a Critical vulnerability (CWE-798).
**Prevention:** Never provide a hardcoded default for secrets. If a secret is missing, either generate a secure random one at runtime (fail-safe) or refuse to start (fail-secure).

## 2025-02-14 - API Key Leakage via Query Parameters
**Vulnerability:** The `/v1/auth/verify` endpoint in `src/ippoc/soma/server.py` accepted API keys via query parameters, causing them to be potentially logged in server access logs and browser history (CWE-598). Additionally, tokens were generated using `uuid.uuid4()`, which is not cryptographically secure.
**Learning:** Convenience in API design (allowing query params for quick testing) often leads to security regressions. Internal services were also configured to use this insecure method, propagating the vulnerability across the system.
**Prevention:** Enforce `Authorization` headers (e.g., Bearer tokens) for all sensitive data transmission. Use `secrets.token_urlsafe()` for token generation instead of `uuid`.
