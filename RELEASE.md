# IPPOC-OS v0.9.0-sovereign | Distribution Guide

This guide provides the necessary information for auditors, developers, and users to verify and deploy the IPPOC platform in its sovereign state.

---

## 1. Provenance & Integrity
Every official release of IPPOC is anchored by a checksum manifest.

### Verify Artifacts
Before installation, verify the integrity of the source:
```bash
sha256sum -c checksums.sha256
```

---

## 2. Professional Installation
IPPOC is designed to be installed into an isolated environment without affecting the host system's global Python namespace.

### Universal Installer
```bash
./install.sh
```
This command:
- Detects OS (Linux/macOS).
- Creates a virtual environment in `~/.ippoc/venv`.
- Installs the `ippoc-platform` package.
- Registers a `ippoc` CLI shim in `~/.local/bin/ippoc`.

---

## 3. Sovereignty Check
To verify that IPPOC is truly standalone, you can run the non-negotiable independence contract:
```bash
# Set PYTHONPATH to include the src/ directory for the test runner
export PYTHONPATH=$(pwd)/src
python3 src/ippoc/cortex/tests/test_independence_no_openclaw.py
```
**Success Criteria**: No structural dependency on OpenClaw or secondary control planes.

---

## 4. Uninstallation
IPPOC respects your system. To remove all associated files, environment, and CLI shims:
```bash
./install.sh --uninstall
```

---

## 5. Licensing
IPPOC is distributed under the **MIT License**.
See `pyproject.toml` for metadata.

---
**IPPOC-OS: Sovereignty in One Command.**
