## 2025-02-06 - Default Insecure Configuration
**Vulnerability:** Hardcoded API key ("ippoc-secret-key") used as default in `src/cortex/cortex/server.py`.
**Learning:** Default configurations for development often make their way into production or expose systems during testing if not explicitly overridden. The system relied on a specific hardcoded string for default auth, which is a Critical vulnerability (CWE-798).
**Prevention:** Never provide a hardcoded default for secrets. If a secret is missing, either generate a secure random one at runtime (fail-safe) or refuse to start (fail-secure).
## 2026-04-06 - Missing Authorization on Admin Endpoint
**Vulnerability:** The `/v1/admin/model_market/update` endpoint lacked proper scope-based authorization checks, allowing any user with a valid API key to modify model costs regardless of their privileges.
**Learning:** Endpoints prefixed with `/admin/` do not automatically inherit administrative privileges; the framework requires explicit scope validation within the handler logic.
**Prevention:** Always verify that administrative routes explicitly call scope-checking functions (e.g., `_authorize_simple(..., "orchestrator:admin")`) inside the endpoint definition to prevent privilege escalation.
