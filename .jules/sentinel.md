## 2025-02-06 - Default Insecure Configuration
**Vulnerability:** Hardcoded API key ("ippoc-secret-key") used as default in `src/cortex/cortex/server.py`.
**Learning:** Default configurations for development often make their way into production or expose systems during testing if not explicitly overridden. The system relied on a specific hardcoded string for default auth, which is a Critical vulnerability (CWE-798).
**Prevention:** Never provide a hardcoded default for secrets. If a secret is missing, either generate a secure random one at runtime (fail-safe) or refuse to start (fail-secure).

## 2024-05-18 - Fix Command and Signal Injection in Thalamus Reflex Rules
**Vulnerability:** The Thalamus agent's reflex rules handled `OOM_KILL` and `HIGH_CPU_USAGE` kernel events by blindly passing the `pid` field from the event payload into `process.kill()` and a shell string interpolated into `cp.exec()`. If an attacker could inject an event with a malicious string in `pid`, they could execute arbitrary shell commands or send signals to arbitrary processes.
**Learning:** Even internal events from systems like kernel event feeds can be untrusted if they derive from user actions or unvalidated external inputs. Direct interpolation into shell commands (`cp.exec()`) and naive type casting for sensitive OS operations (`process.kill()`) bypass type safety mechanisms.
**Prevention:** Always parse and validate untrusted parameters intended for system calls. Verify that IDs meant to be numeric actually are (e.g., `Number.isInteger(Number(pid))`). Prefer executing binaries directly with arguments via `cp.execFile` or `cp.spawn` over relying on shell evaluation with `cp.exec`.
