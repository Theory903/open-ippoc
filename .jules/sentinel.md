## 2025-02-06 - Default Insecure Configuration
**Vulnerability:** Hardcoded API key ("ippoc-secret-key") used as default in `src/cortex/cortex/server.py`.
**Learning:** Default configurations for development often make their way into production or expose systems during testing if not explicitly overridden. The system relied on a specific hardcoded string for default auth, which is a Critical vulnerability (CWE-798).
**Prevention:** Never provide a hardcoded default for secrets. If a secret is missing, either generate a secure random one at runtime (fail-safe) or refuse to start (fail-secure).

## 2025-02-06 - Weak API Key Generation
**Vulnerability:** API keys in `src/ippoc/soma/server.py` were generated using `uuid.uuid4()`.
**Learning:** `uuid.uuid4()` uses a pseudo-random number generator that is not cryptographically secure and may allow attackers to predict keys. The Soma Identity & Trust Service is responsible for generating auth tokens and should use a CSPRNG.
**Prevention:** Always use `secrets` module (e.g., `secrets.token_urlsafe()`) for generating authentication tokens, passwords, and API keys.
