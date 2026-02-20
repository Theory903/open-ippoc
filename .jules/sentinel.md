## 2025-02-06 - Default Insecure Configuration
**Vulnerability:** Hardcoded API key ("ippoc-secret-key") used as default in `src/cortex/cortex/server.py`.
**Learning:** Default configurations for development often make their way into production or expose systems during testing if not explicitly overridden. The system relied on a specific hardcoded string for default auth, which is a Critical vulnerability (CWE-798).
**Prevention:** Never provide a hardcoded default for secrets. If a secret is missing, either generate a secure random one at runtime (fail-safe) or refuse to start (fail-secure).

## 2025-02-06 - Sensitive Data in URLs
**Vulnerability:** API key passed via query parameter (`?api_key=...`) in `/v1/auth/verify`.
**Learning:** Sensitive data in URLs is logged by servers, proxies, and browsers, leading to credential leakage. This pattern was pervasive across multiple internal clients.
**Prevention:** Always use `Authorization` headers (e.g., Bearer token) for transmitting secrets. Use `HTTPBearer` in FastAPI to enforce this structure.
