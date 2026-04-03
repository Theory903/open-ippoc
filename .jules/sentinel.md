## 2025-02-06 - Default Insecure Configuration
**Vulnerability:** Hardcoded API key ("ippoc-secret-key") used as default in `src/cortex/cortex/server.py`.
**Learning:** Default configurations for development often make their way into production or expose systems during testing if not explicitly overridden. The system relied on a specific hardcoded string for default auth, which is a Critical vulnerability (CWE-798).
**Prevention:** Never provide a hardcoded default for secrets. If a secret is missing, either generate a secure random one at runtime (fail-safe) or refuse to start (fail-secure).

## 2025-04-03 - Hardcoded IPPOC_API_KEY Vulnerability
**Vulnerability:** A critical vulnerability was found in `infra/src/cortex/cortex/server.py` where the `IPPOC_API_KEY` defaulted to a hardcoded string `"ippoc-secret-key"` if not provided via an environment variable. Additionally, the production environment check did not enforce authentication strictly.
**Learning:** Hardcoded credentials provide a default attack vector if the deployment environment is misconfigured. In AI orchestration systems, relying on default fallback secrets can compromise the entire node mesh.
**Prevention:** Never use static strings as fallback secrets in code. Always generate a random, secure default (e.g., via `secrets.token_hex(32)`) if an API key is absent, and log a loud security warning so the deployment misconfiguration is noticed immediately. Explicitly override any configuration that could disable authentication in a production environment.
