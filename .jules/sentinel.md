## 2025-02-06 - Default Insecure Configuration
**Vulnerability:** Hardcoded API key ("ippoc-secret-key") used as default in `src/cortex/cortex/server.py`.
**Learning:** Default configurations for development often make their way into production or expose systems during testing if not explicitly overridden. The system relied on a specific hardcoded string for default auth, which is a Critical vulnerability (CWE-798).
**Prevention:** Never provide a hardcoded default for secrets. If a secret is missing, either generate a secure random one at runtime (fail-safe) or refuse to start (fail-secure).

## 2025-02-06 - Insecure Auth Token Generation
**Vulnerability:** The `/v1/auth/issue` endpoint in `src/ippoc/soma/server.py` allowed any caller to generate valid API keys.
**Learning:** Default unauthenticated endpoints for testing local features in production or shared environments can be abused. Missing host or source IP verification provides unauthorized access vectors.
**Prevention:** Implement strict client host verification (e.g., checking for `127.0.0.1`, `::1`, `localhost`, `testserver`) to restrict administrative or key issuance actions exclusively to trusted loopback interfaces or authenticated callers.
