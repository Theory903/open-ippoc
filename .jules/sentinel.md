## 2025-02-06 - Default Insecure Configuration
**Vulnerability:** Hardcoded API key ("ippoc-secret-key") used as default in `src/cortex/cortex/server.py`.
**Learning:** Default configurations for development often make their way into production or expose systems during testing if not explicitly overridden. The system relied on a specific hardcoded string for default auth, which is a Critical vulnerability (CWE-798).
**Prevention:** Never provide a hardcoded default for secrets. If a secret is missing, either generate a secure random one at runtime (fail-safe) or refuse to start (fail-secure).

## 2026-03-05 - Unauthenticated API key issuance
**Vulnerability:** The Soma service (`src/ippoc/soma/server.py`) allowed anyone to issue an API key without authentication via `POST /v1/auth/issue`, which is a critical security risk (CWE-285).
**Learning:** Endpoints meant for internal bootstrap or administrative use (like generating an API key for the first time) were left exposed without network-level or authentication restrictions. This bypasses access controls and can grant unauthorized actors API keys.
**Prevention:** Always secure administrative or bootstrap endpoints. If an endpoint must be unauthenticated to allow local system setup, explicitly restrict it to the local loopback interface (`127.0.0.1` / `::1`) by validating `request.client.host` to prevent remote exploitation.
