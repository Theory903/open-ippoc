## 2025-02-06 - Default Insecure Configuration
**Vulnerability:** Hardcoded API key ("ippoc-secret-key") used as default in `src/cortex/cortex/server.py`.
**Learning:** Default configurations for development often make their way into production or expose systems during testing if not explicitly overridden. The system relied on a specific hardcoded string for default auth, which is a Critical vulnerability (CWE-798).
**Prevention:** Never provide a hardcoded default for secrets. If a secret is missing, either generate a secure random one at runtime (fail-safe) or refuse to start (fail-secure).
## 2024-03-03 - Weak API Key Generation
**Vulnerability:** API keys in `src/ippoc/soma/server.py` were generated using `uuid.uuid4()`.
**Learning:** UUID v4 is designed for uniqueness, not cryptographic security. It uses a pseudo-random number generator that might be predictable, making brute-forcing or predicting API keys easier.
**Prevention:** Always use a cryptographically secure random number generator (CSPRNG), like Python's `secrets` module, for generating API keys, tokens, or passwords.
