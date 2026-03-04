## 2025-02-06 - Default Insecure Configuration
**Vulnerability:** Hardcoded API key ("ippoc-secret-key") used as default in `src/cortex/cortex/server.py`.
**Learning:** Default configurations for development often make their way into production or expose systems during testing if not explicitly overridden. The system relied on a specific hardcoded string for default auth, which is a Critical vulnerability (CWE-798).
**Prevention:** Never provide a hardcoded default for secrets. If a secret is missing, either generate a secure random one at runtime (fail-safe) or refuse to start (fail-secure).
## 2025-03-04 - Insecure API Key Generation
**Vulnerability:** Weak random number generation using `uuid.uuid4()` for API keys in `src/ippoc/soma/server.py`.
**Learning:** `uuid.uuid4()` is not designed for cryptographic security and can be predictable. It provides less entropy than required for secure API keys.
**Prevention:** Always use the `secrets` module (e.g., `secrets.token_urlsafe(32)`) for generating cryptographically secure random strings for passwords, tokens, and API keys.
