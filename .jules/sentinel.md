## 2025-02-06 - Default Insecure Configuration
**Vulnerability:** Hardcoded API key ("ippoc-secret-key") used as default in `src/cortex/cortex/server.py`.
**Learning:** Default configurations for development often make their way into production or expose systems during testing if not explicitly overridden. The system relied on a specific hardcoded string for default auth, which is a Critical vulnerability (CWE-798).
**Prevention:** Never provide a hardcoded default for secrets. If a secret is missing, either generate a secure random one at runtime (fail-safe) or refuse to start (fail-secure).

## 2025-02-06 - Remote API Key Issuance
**Vulnerability:** Unauthenticated remote access to API key generation via `/v1/auth/issue`.
**Learning:** Missing loopback or authentication checks on admin/provisioning endpoints expose the entire auth chain to attackers, allowing anyone to mint admin keys.
**Prevention:** Restrict token issuance and admin endpoints to localhost (e.g. `127.0.0.1`, `::1`) unless specifically authenticated.
