## 2025-02-06 - Default Insecure Configuration
**Vulnerability:** Hardcoded API key ("ippoc-secret-key") used as default in `src/cortex/cortex/server.py`.
**Learning:** Default configurations for development often make their way into production or expose systems during testing if not explicitly overridden. The system relied on a specific hardcoded string for default auth, which is a Critical vulnerability (CWE-798).
**Prevention:** Never provide a hardcoded default for secrets. If a secret is missing, either generate a secure random one at runtime (fail-safe) or refuse to start (fail-secure).
## 2025-02-06 - Mirrored Default Insecure Configurations
**Vulnerability:** Hardcoded API key ("ippoc-secret-key") used as default in `infra/src/cortex/cortex/server.py` mirroring the identical vulnerability in `src/ippoc/cortex/cortex/server.py`.
**Learning:** Default configurations containing hardcoded secrets often propagate across mirrored directories and infrastructure deployment templates if not audited globally across the repo.
**Prevention:** When patching a vulnerability, always use tools like `find` and `grep` to hunt for duplicate files or equivalent components across the entire mono-repo (such as the `infra/src` mirror) rather than assuming a fix in `src/` covers all deployment vectors.
