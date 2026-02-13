## 2025-02-06 - Default Insecure Configuration
**Vulnerability:** Hardcoded API key ("ippoc-secret-key") used as default in `src/cortex/cortex/server.py`.
**Learning:** Default configurations for development often make their way into production or expose systems during testing if not explicitly overridden. The system relied on a specific hardcoded string for default auth, which is a Critical vulnerability (CWE-798).
**Prevention:** Never provide a hardcoded default for secrets. If a secret is missing, either generate a secure random one at runtime (fail-safe) or refuse to start (fail-secure).

## 2025-02-06 - Secrets in URL Parameters
**Vulnerability:** API keys transmitted as query parameters in `Soma` authentication service (`/v1/auth/verify?api_key=...`).
**Learning:** Frameworks like FastAPI default to query parameters for simple string arguments, making it easy to accidentally expose secrets in access logs and browser history (CWE-598).
**Prevention:** Explicitly use `Security(HTTPBearer)` or `Header` dependencies for sensitive data. Audit all endpoints accepting secrets to ensure they are not using query parameters.
