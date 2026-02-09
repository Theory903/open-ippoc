# Changelog

All notable changes to IPPOC-OS will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.0.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [v0.9.0] - 2026-02-09 (Sovereign Release)

### Added
- **Dynamic Path Discovery**: All core tools (Cerebellum, WorldModel) now locate resources relative to `__file__`, eliminating hardcoded paths.
- **Improved CLI**: `ippoc` command now installed as a proper entry point via `pip`.
- **Integrity Manifest**: `checksums.sha256` generated for core release artifacts.
- **Distribution Guide**: `RELEASE.md` added for third-party auditors.
- **Hostile Audit Tests**: `test_hostile_audit.py` added to verify CAP-01 enforcement.

### Changed
- **Namespace Refactor**: Moved all core logic to `src/ippoc` for proper Python packaging.
- **Orchestrator Security**: Fixed a critical precedence bug in CAP-01 (Capability Law) enforcement. ACTOR tools can now perform deletes, while SENSOR tools are strictly read-only.
- **Metadata**: Updated `pyproject.toml` with canonical PEP 440 versioning and release-grade metadata.
- **CLI Resilience**: `ippoc status` now degrades gracefully when the core is offline.

### Removed
- **Hardcoded Paths**: Removed absolute paths from `install.sh`, `generate_openclaw_fs.sh`, and documentation.
- **Development Artifacts**: Excluded `dist`, `target`, `node_modules`, `tests`, `legacy`, and `experiments` from the distribution build.

### Security
- **CAP-01 Enforcement**: Validated via hostile review (Phase XIV.2).
- **Independence Contract**: Validated via `test_independence_no_openclaw.py`.
