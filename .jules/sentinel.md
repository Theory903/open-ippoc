## 2025-02-06 - Default Insecure Configuration
**Vulnerability:** Hardcoded API key ("ippoc-secret-key") used as default in `src/cortex/cortex/server.py`.
**Learning:** Default configurations for development often make their way into production or expose systems during testing if not explicitly overridden. The system relied on a specific hardcoded string for default auth, which is a Critical vulnerability (CWE-798).
**Prevention:** Never provide a hardcoded default for secrets. If a secret is missing, either generate a secure random one at runtime (fail-safe) or refuse to start (fail-secure).

## 2025-02-17 - Weak Cryptography for Secrets
**Vulnerability:** Weak API Key Generation using UUIDv4 in `src/ippoc/soma/server.py`.
**Learning:** Developers often use UUIDs as "unique enough" strings for secrets, but they lack cryptographic entropy and are predictable (CWE-330). This allows attackers to potentially guess keys or narrow the search space significantly.
**Prevention:** Always use `secrets.token_urlsafe()` or `secrets.token_hex()` for generating authentication tokens, API keys, and session identifiers. Avoid `uuid` and `random` for security contexts.
