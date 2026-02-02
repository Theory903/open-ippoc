# IPPOC-OS Git Protocol & Governance

This document defines the non-negotiable laws governing Git operations and evolution within the IPPOC-OS repository.

## 1. The Atomic Commit Protocol (Rule 17)

Every commit MUST follow the structured "organ: intent" format. 

### 1.1 Subject Line
Format: `<organ>/<subsystem>: <short intent>`
Example: `body/immune: improve git flow`

Allowed Organs: `brain`, `body`, `mind`, `memory`, `infra`, `system`, `docs`, `api`.

### 1.2 Message Body
Every commit message MUST contain two mandatory sections:

- **DESCRIPTION**: A clear, multi-line explanation of WHY the change was made and WHAT it solves.
- **IMPACT**: A summary of the expected behavioral changes, safety considerations, or performance implications.

---

## 2. Feature-Branch Strategy (Rule 6 & Rule 12)

Strict isolation is mandatory for all mutations.

1. **Isolation**: No work is performed directly on `main`. Every change starts in a `feature/<name>` branch.
2. **Simulation**: Mutations must pass `cargo check` and `npm lint` on the feature branch before being considered for merge.
3. **Formal Merge**: Merges into `main` MUST use `--no-ff` (non-fast-forward) to preserve the historical boundary of the feature.

---

## 3. Autonomous Evolution & Immunity

The system's "Immune System" (body/immune) and the "Evolution Engine" (brain/evolution) govern all automated updates.

### 3.1 Patch Review
Before a branch is even created, the brain MUST perform a Reasoning Audit:
- **Rule 6 Check**: Verify the patch does not exceed 300 LOC.
- **Governance Scan**: Check against `rules.md` for Canon violations.
- **Immune Reject**: If any violation is detected, the immune system MUST reject the mutation.

### 3.2 Auto-Commit Intelligence
When performing autonomous mutations, the brain MUST:
1. Use `summarize_staged_changes` to inspect the diff.
2. Generate professional `DESCRIPTION` and `IMPACT` metadata based on the simulation results.
3. Use the `commit_staged` API to apply the mutation with full protocol compliance.

---

## 4. Enforcement

- **GitHub Actions**: Automated linting (`check-protocol.yml`) will block any PR that violates these rules.
- **Rules File**: These rules-v2 took effect on 2026-02-01 and are an extension of the Prime Directive.
