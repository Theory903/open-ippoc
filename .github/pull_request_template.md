# IPPOC-OS Pull Request Template

## 1. Intent Declaration (MANDATORY)

**What organ does this PR affect?**
- [ ] `brain` (Reasoning - Python/Rust)
- [ ] `body` (Runtime/Mesh - Rust)
- [ ] `mind` (Interface - TS/Front-end)
- [ ] `memory` (Data - SQL/Vectors)
- [ ] `docs` only

**Change Type**
- [ ] bug fix
- [ ] feature
- [ ] refactor
- [ ] documentation
- [ ] evolution logic

---

## 2. Canon Compliance

- [ ] I read `docs/prds/00_SYSTEM_CANON.md`
- [ ] I read the relevant organ PRD (`01_BRAIN`, `02_BODY`, etc.)
- [ ] This PR does **NOT** violate organ boundaries (e.g., Brain calling OS directly)
- [ ] This PR does **NOT** touch `invariants/` (Automatic Reject if checked)

---

## 3. Scope Control

- **Files modified**: 
- **Concepts modified**: (One sentence summary)
- **LOC changed**: (aim for < 300 LOC per conceptual change)

☑ I confirm this PR modifies the **smallest viable surface**.

---

## 4. IPPOC-FS Contract Compliance

- [ ] All modified directories contain a valid `__init__.py` or `mod.rs` mapping file.
- [ ] Public functions include **AI-readable docstrings** (PURPOSE, INPUT, OUTPUT, SIDE EFFECTS).
- [ ] No new `utils`, `helpers`, or ambiguous names added. Names reflect biological role.
- [ ] **Traversal Test**: An AI agent reading ONLY the `docs/spec` and `__init__`/`mod.rs` files can understand where to find this code.

---

## 5. Boundary Declaration

**This PR CALLS:**
- [ ] Same organ only
- [ ] Allowed cross-organ APIs (e.g., Brain -> Body API)
- [ ] **VIOLATION**: Cross-organ direct calls (e.g., Brain -> Memory direct write)

**List External APIs used**:
- 

---

## 6. Safety & Evolution Impact

- [ ] No side effects added (or explicitly documented)
- [ ] No irreversible behavior
- [ ] Rollback steps identified
- [ ] Evolution logic unchanged OR explicitly documented in `docs/prds/06_EVOLUTION_SPEC.md`

---

## 7. Final Assertion (REQUIRED)

> I affirm this PR follows the **IPPOC-FS traversal rules** and can be safely understood, modified, or reverted by a future AI agent without additional context.

**Author Signature**: ___________________
