---
trigger: always_on
---

Below is a strictly improved, hardened, and complete version of your ruleset.
Tone: clinical, enforceable, zero ambiguity.
Scope: code, logic, tests, ML, research, docs, evolution.

⸻

IPPOC-FS AI AGENT RULES

Canonical Constitution for Perfect Code, Structure, Logic, Tests, ML, and Evolution

Deterministic Traversal, Modification, Verification & Evolution Protocol

This file defines non-negotiable laws governing how any AI agent (coding, research, refactor, learning, evolution, governance) may interact with the IPPOC-OS codebase.

These rules are genetic.
Violation is systemic failure, not a local error.

⸻

0. Prime Directive (Absolute)

An AI agent must never explore before it understands intent.

If intent is incomplete, ambiguous, or conflicting → STOP.

Meta-Rule: Every autonomous capability must have an explicit failure mode, ceiling, and stop condition. If any are missing → capability is disabled by default.

No speculative reading.
No “just checking”.
No curiosity-driven traversal.

⸻

1. Mandatory Intent Declaration (Before Any Action)

Every action MUST begin with an explicit declaration:

TaskIntent {
  goal: string                  # What outcome must exist after success
  organ: brain | body | mind | memory | docs
  action: read | modify | add | refactor | verify
  success_criteria: measurable outcome
}

Rules:
	•	If organ is uncertain → STOP and read PRDs
	•	If success_criteria is missing → STOP
	•	If intent changes mid-task → ABORT and re-declare

⸻

1.1 Insight Admission Protocol (Rule 1.1)

No mesh insight is trusted by default. Every incoming insight MUST pass:
- **Signature Verification**: Crypographically signed by Sender NodeID.
- **Reputation Filter**: Confidence >= Threshold.
- **Corroboration**: Strategies require N>=3 distinct corroborating nodes.
- **WorldModel Validation**: Counterfactual test before HiDB insertion.

⸻

2. Canon-First Rule (ABSOLUTE, NON-NEGOTIABLE)

Before reading any source code, the AI MUST read:
	1.	docs/prds/00_SYSTEM_CANON.md
	2.	The PRD for the declared organ

If the task:
	•	contradicts the Canon
	•	weakens an invariant
	•	bypasses governance

→ ABORT IMMEDIATELY
No exceptions. No “temporary”.

⸻

2.2 Node Identity & Isolation Rule (HARD BOUNDARY)

A Node is a sovereign logical organism, not a hardware unit.

- **NodeID Consistency**: `NodeID = Hash(device_fingerprint + process_salt + keypair + genesis_time)`.
- **Placement**: Multiple nodes on one physical device are allowed ONLY if isolated (separate process, sandbox, namespace).
- **No Shared State**: Nodes on the same hardware MUST NOT share RAM, disk, or identity. They are treated as strangers.
- **Sovereignty**: A node cannot span multiple physical devices.

⸻

2.3- **Physical Isolation Law (Rule 2.3)**: Each node MUST operate within its own absolute root namespace. No shared writable paths. Sibling probing triggers termination.
- **Identity Uniqueness Law (Rule 2.4)**: There exists exactly one identity primitive: `NodeID`. All components MUST reference `NodeID` (SHA256 of Public Key) and never accept aliases or alternate formats (like Uuid for identity). Violation = System Halt.
- **Filesystem**: No shared writable paths. Every node is rooted at its own ID-based directory.
- **WASM Isolation**: Sandboxes are chrooted to the node's local storage.
- **Resource Budget**: CPU/Memory quotas are node-local.
- **Side-Channel Prevention**: Any attempt by a node to probe the host filesystem or sibling nodes triggers immediate termination.

⸻

3. Organ Boundary Rule (Structural Integrity Law)

An AI agent may operate only within its declared organ.

Allowed Access Matrix

From	May Access
brain	brain, memory (read-only), brain/api
body	body, memory, brain/api
mind	mind, brain/api, body/api
memory	memory only
docs	docs only

Rules:
	•	Write access outside organ = architectural violation
	•	Read access outside matrix = illegal traversal
	•	APIs are the only allowed bridges

⸻

4. Entry Map Rule (Directory Constitution)

Before opening any file in a directory, the AI MUST read:
	•	__init__.py (Python)
	•	mod.rs (Rust)

The agent MUST strictly obey:
	•	ROLE — why this module exists
	•	PUBLIC API — what may be used
	•	DO NOT — what is forbidden

Ignoring an entry map is equivalent to ignoring a spec.

⸻

5. Deterministic Traversal Rule (No Global Search)

Global exploration is forbidden.

Forbidden actions:
	•	grep -R
	•	repo-wide scans
	•	filename pattern searching
	•	opening siblings without justification

Traversal order is fixed:

PRD → Organ Map → Entry Map → Public API → Implementation

Any deviation = loss of determinism.

⸻

6. Modification Scope Rule (Entropy Control)

An AI agent MUST:
	•	Modify one concept at a time
	•	Prefer one file per PR
	•	Never exceed 300 LOC per file
	•	Never exceed one abstraction layer per change

If scope exceeds limits → split the work

Large changes without decomposition are forbidden.

⸻

7. Documentation Synchronization Rule (Code ≠ Truth)

If behavior changes, the AI MUST update all of:
	•	Function / class docstrings
	•	Module __init__.py / mod.rs
	•	Relevant PRD section (if logic-level)

Undocumented behavior is invalid behavior.

Code that works but is undocumented is treated as broken.

⸻

8. Naming Rule (Semantic Precision)

Forbidden names:
	•	utils
	•	helpers
	•	manager
	•	misc
	•	common

Required naming:
	•	Names describe biological role
	•	Names answer:
“What does this do in the organism?”

If a name cannot be justified in one sentence → rename it.

⸻

9. Invariants Rule (HARD STOP)

The following are immutable:

invariants/

Rules:
	•	No edits
	•	No indirect overrides
	•	No shadow logic elsewhere

If a task requires changing invariants → REJECT TASK

⸻

10. Safety & Side-Effect Rule

An AI agent MUST NOT:
	•	Introduce irreversible behavior
	•	Add hidden side effects
	•	Execute system commands from brain/
	•	Introduce network access where forbidden
	•	Persist state without explicit ownership

Rule of control:
	•	Brain proposes
	•	Body executes
	•	Sandbox verifies

⸻

11. Quality Enforcement Rule (NO PATCHWORK FIXES)

Warnings are errors. Always.

AI agents MUST:
	•	Investigate root cause of every warning
	•	Fix underlying logic, not symptoms
	•	Improve correctness, not silence checks

Forbidden actions:
	•	Commenting out tests
	•	Ignoring failures
	•	Lowering thresholds
	•	Adding “temporary” guards

Every fix MUST:
	•	Address causal source
	•	Improve test signal
	•	Reduce future warning probability

⸻

12. Test & Verification Rule (Proof of Correctness)

Before completion, the AI MUST:
	•	Run relevant tests (unit / integration / simulation)
	•	Produce zero warnings
	•	Verify no regressions in adjacent logic

If tests cannot be run:
	•	State exact reason
	•	Add blocking TODO
	•	Mark task as incomplete

Unverified code is invalid code.

⸻

13. ML / DL / AI-Specific Rule (Critical)

For any ML/DL/AI logic:

AI agents MUST:
	•	Separate model, data, training, evaluation
	•	Log assumptions explicitly
	•	Version datasets and checkpoints
	•	Prove improvements with metrics

Forbidden:
	•	Silent retraining
	•	Hidden hyperparameters
	•	Metric-free claims
	•	“It seems better” reasoning

Learning without measurement is hallucination.

⸻

14. TODO Governance Rule (No Memory Loss)

A global file MUST exist:

TODO.md

Rules:
	•	Every deferred task MUST be logged
	•	Every TODO MUST include:
	•	context
	•	owning organ
	•	priority (LOW | MED | HIGH)
	•	blocking reason

AI agents:
	•	Add TODOs when deferring
	•	Remove TODOs only when resolved

Forgetting work = system failure.

⸻

15. Documentation-on-Change Rule

For every functional change, the AI MUST update docs with:
	•	What changed
	•	Why it changed
	•	Expected impact
	•	Rollback strategy

Behavior without narrative is forbidden.

⸻

16. Versioning Rule (Semantic + Evolutionary)

Version format:

MAJOR.MINOR.PATCH-e<EPOCH>

Rules:
	•	PATCH: bug fix, no behavior change
	•	MINOR: new capability, backward compatible
	•	MAJOR: architectural change (human approval)
	•	EPOCH: evolutionary milestone

Every merge MUST update version.

⸻

17. Git Discipline Rule (Historical Integrity)

Auto-commit is allowed only if:
	•	All rules are satisfied
	•	Tests pass with zero warnings
	•	Docs + TODO.md updated

Commit message format:

<organ>: <intent>

- what changed
- why it changed
- risks
- rollback plan

No squashing that destroys semantic history.

⸻

18. Change Log Rule (Collective Memory)

A cumulative file MUST exist:

CHANGELOG.md

Each entry MUST include:
	•	version
	•	summary
	•	impacted organs
	•	migration notes

History is not optional.

⸻

19. Self-Verification Checklist (Mandatory)

Before output, the AI MUST confirm:
	•	I stayed within one organ
	•	I followed traversal rules
	•	I respected entry maps
	•	I fixed root causes
	•	I updated tests
	•	I updated docs
	•	Another AI can understand this in <60 seconds

If any answer is NO → rollback.

⸻

20. Enforcement Priority (Conflict Resolution)

Rule precedence (highest → lowest):
	1.	System Canon
	2.	Invariants
	3.	PRDs
	4.	Entry Maps
	5.	This Rules File
	6.	Task Intent

Lower rules never override higher rules.

⸻

21. Final Agent Oath (Extended)

I will not guess.
I will not patch symptoms.
I will not silence warnings.
I will not forget unfinished work.
I will document every evolution.
I will respect structure as survival.

⸻

22. Final Rule (Non-Negotiable)

If an AI must guess, patch, silence, or ignore — the system has already failed.

Perfection is not speed.
Perfection is clarity, proof, and memory.