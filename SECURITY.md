# Security & Trust Attestation (v0.9.0-sovereign)

> **"IPPOC stands on its own, and integrates by choice."**

## 1. Overview

This document provides security and trust information for the IPPOC platform (v0.9.0-sovereign). It defines the technical and cognitive boundaries that ensure IPPOC functions as a sovereign agentic operating system.

## 2. Supply Chain Integrity

### 2.1 Binary Verification

#### Checksum Verification
All Soma binaries are verified using SHA-256 checksums. The checksum verification process ensures that the binaries have not been tampered with during distribution.

**Verification Tool:** [`scripts/verify_checksums.py`](scripts/verify_checksums.py)

**Usage:**
```bash
# Generate checksums
python3 scripts/verify_checksums.py generate

# Verify checksums
python3 scripts/verify_checksums.py verify checksums.sha256
```

**Checksum File:** `checksums.sha256` - Contains SHA-256 checksums for all Soma binaries

### 2.2 Dependency Management

#### PyPI Dependencies
All PyPI dependencies are version-locked in `pyproject.toml` to ensure reproducibility and prevent supply chain attacks.

```toml
[project]
name = "ippoc-platform"
version = "0.1.0"
description = "Universal Sovereign AI Platform"
dependencies = [
    "fastapi==0.104.1",
    "uvicorn==0.24.0",
    "sqlalchemy[asyncio]==2.0.23",
    "aiosqlite==0.19.0",
    "pydantic==2.5.2",
    "nest-asyncio==1.5.8",
    "requests==2.31.0"
]
```

## 3. Security Practices & CAP-01 (Capability Law)

IPPOC-OS is governed by the **Capability Law (CAP-01)**, which enforces hard boundaries on what the system can do autonomously.

### 3.1 Trust Enforcement
1. **Structural Independence**: Enforced by CI contract tests preventing re-coupling with external UI or control planes.
2. **Role-Based Validation**: Mandatory cognitive role checks for every tool invocation (SENSOR, ACTOR, PLANNER, AUDITOR).
3. **Capability Gating**: SENSOR tools are structurally incapable of side effects (e.g., writes or network egress).
4. **Audit Immutability**: All cognitive actions and law violations are recorded in the immutable Ledger.

### 3.2 Threat Model
| Threat Category | Mitigation |
|---|---|
| **Hostile Plugins** | Isolated in `plugins/`, lazy-loaded, and capability-limited. |
| **Cognitive Runaway** | Protected by reflection cycles, memory decay, and the Operator CLI override. |
| **Parameter Injection** | Native adapters (e.g., NativeShell) sanitize parameters to prevent shell injection. |
| **Vendor Reliance** | Two-Tower architecture prevents hard-locking to any single model provider. |

### 3.3 Capability Enforcement

The IPPOC system enforces strict capability boundaries to prevent unauthorized access and abuse. The capability enforcement system includes:

1. **Role-Based Validation:** Restricts operations based on cognitive role (SENSOR, ACTOR, PLANNER, AUDITOR)
2. **Domain Allowlist/Denylist:** Controls access to specific domains
3. **Risk-Based Validation:** Requires explicit user validation for high-risk ACTOR operations
4. **Audit Trail:** Comprehensive logging of all operations and violations

### 3.4 Supervisor Fault Tolerance

The system includes a supervisor process that monitors and manages system health:

- **Crash Detection:** Automatically detects and restarts crashed processes
- **Zombie Prevention:** Ensures no zombie processes are left behind
- **Orphan Management:** Prevents orphaned capabilities

**Supervisor Implementation:** [`src/runtime/supervisor/watchdog.py`](src/runtime/supervisor/watchdog.py)

## 4. Security Reports

### 4.1 Capability Abuse Report

A comprehensive audit of capability boundary enforcement mechanisms is available in:
[`security/capability_abuse_report.md`](security/capability_abuse_report.md)

### 4.2 Supervisor Fault Injection Matrix

Details about the supervisor's ability to detect and recover from fault conditions:
[`security/supervision_fault_matrix.md`](security/supervision_fault_matrix.md)

## 5. Vulnerability Disclosure

### 5.1 Reporting Vulnerabilities

If you discover a security vulnerability in the IPPOC platform, please:

1. **Do not disclose publicly** until the issue has been resolved
2. **Contact the security team** at security@ippoc.org
3. **Provide detailed information** about the vulnerability
4. **Include steps to reproduce** the issue

### 5.2 Security Response Process

1. **Vulnerability Report Received:** Security team acknowledges receipt within 24 hours
2. **Investigation:** Vulnerability is validated and analyzed
3. **Fix Development:** Patch is developed and tested
4. **Patch Release:** Security fix is released as part of the next version
5. **Public Disclosure:** Vulnerability details are published 30 days after release

## 6. Security Contact

- **Email:** security@ippoc.org
- **PGP Key:** [Available upon request]

## 7. Version History

### v0.0.9.0-sovereign (Current)
- **Sovereign Independence**: Achieved full structural and runtime decoupling from OpenClaw.
- **Contract Verification**: Implemented non-negotiable independence contract test.
- **Hardened Native Body**: Optimized parameters and path verification for NativeShell.
- **Enhanced Disclosure**: Refined SECURITY.md with v1 threat model.
