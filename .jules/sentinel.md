## 2025-02-06 - Default Insecure Configuration
**Vulnerability:** Hardcoded API key ("ippoc-secret-key") used as default in `src/cortex/cortex/server.py`.
**Learning:** Default configurations for development often make their way into production or expose systems during testing if not explicitly overridden. The system relied on a specific hardcoded string for default auth, which is a Critical vulnerability (CWE-798).
**Prevention:** Never provide a hardcoded default for secrets. If a secret is missing, either generate a secure random one at runtime (fail-safe) or refuse to start (fail-secure).

## 2026-02-22 - Weak Randomness in Secrets Generation
**Vulnerability:** Use of `uuid.uuid4()` for API key generation in `src/ippoc/soma/server.py`.
**Learning:** UUIDs are designed for uniqueness, not unpredictability. While v4 uses random bits, it is not a cryptographic primitive and exposes structure. Using it for secrets (like API keys) weakens the security posture (CWE-330).
**Prevention:** Use `secrets.token_urlsafe()` or `secrets.token_hex()` which are designed for generating cryptographically strong random numbers suitable for managing data such as passwords, account authentication, security tokens, and related secrets.
