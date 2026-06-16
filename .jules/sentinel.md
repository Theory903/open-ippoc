## 2025-02-06 - Default Insecure Configuration
**Vulnerability:** Hardcoded API key ("ippoc-secret-key") used as default in `src/cortex/cortex/server.py`.
**Learning:** Default configurations for development often make their way into production or expose systems during testing if not explicitly overridden. The system relied on a specific hardcoded string for default auth, which is a Critical vulnerability (CWE-798).
**Prevention:** Never provide a hardcoded default for secrets. If a secret is missing, either generate a secure random one at runtime (fail-safe) or refuse to start (fail-secure).

## 2025-05-06 - Command Injection via KERNEL_EVENT
**Vulnerability:** Command injection vulnerability in Thalamus agent where unvalidated PID from a KERNEL_EVENT payload was directly interpolated into `cp.exec` for process throttling.
**Learning:** Relying on `cp.exec` with shell interpolation for system administration commands (like `renice`) creates critical vulnerabilities if the underlying event source can be manipulated or forged, even internally. `exec` invokes a shell, making it unsafe for untrusted input.
**Prevention:** Always use `cp.execFile` or `cp.spawn` with arguments passed as an array to strictly separate the executable command from its data arguments, neutralizing shell injection risks.
