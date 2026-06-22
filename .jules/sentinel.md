## 2025-02-06 - Default Insecure Configuration
**Vulnerability:** Hardcoded API key ("ippoc-secret-key") used as default in `src/cortex/cortex/server.py`.
**Learning:** Default configurations for development often make their way into production or expose systems during testing if not explicitly overridden. The system relied on a specific hardcoded string for default auth, which is a Critical vulnerability (CWE-798).
**Prevention:** Never provide a hardcoded default for secrets. If a secret is missing, either generate a secure random one at runtime (fail-safe) or refuse to start (fail-secure).
## 2025-02-28 - [Implement forget functionality]
**Vulnerability:** Not a vulnerability, but a partial/buggy uncommitted optimization blocked the proper feature.
**Learning:** Checking whether variables like bool vs int evaluate differently is crucial (`bool` is subclass of `int`). We need to explicitly check `type(res) is bool` vs `type(res) is int` when dealing with systems that mix the two.
**Prevention:** In heterogeneous subsystem interfaces, enforce standardized return types, or rely on explicit types instead of duck typing for counting.
