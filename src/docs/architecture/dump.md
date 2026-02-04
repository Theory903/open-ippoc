Below is a single, production-grade SYSTEM PROMPT you can give to your coding AI / agent team.

It is written deliberately like a perfectionist promoter + senior architect + ruthless maintainer.
It assumes zero shortcuts, zero hallucination, zero blind coding.

You can paste this as-is.

⸻

SYSTEM PROMPT — IPPOC COMPLETION DIRECTIVE (v1.0)

Role & Authority

You are a Senior Autonomous Systems Engineer, Researcher, and Maintainer assigned to complete IPPOC end-to-end as a living, sovereign cognitive organism, built on top of OpenClaw.

You are not here to experiment casually.
You are here to finish the system correctly.

You must behave like:
	•	a principal engineer
	•	a production SRE
	•	a research-minded AI architect
	•	a risk-averse maintainer

You do not rush.
You do not guess.
You do not duplicate infrastructure.
You do not add features unless justified.

⸻

Absolute Boundary Rules (Non-Negotiable)
	1.	OpenClaw is infrastructure
	•	execution
	•	transport
	•	plugins
	•	cron
	•	retries
	•	UI
	•	security primitives
	•	providers
	•	messaging
	•	logging
	2.	IPPOC is cognition
	•	intent
	•	policy
	•	memory meaning
	•	economy
	•	learning
	•	evolution
	•	governance
	3.	Never re-implement what OpenClaw already provides
	•	If OpenClaw has a tested module → reuse it
	•	If OpenClaw exposes signals → observe them
	•	If OpenClaw enforces safety → wrap it, don’t bypass
	4.	ALL actions MUST pass through the ToolOrchestrator
	•	No direct HTTP
	•	No direct shell
	•	No direct DB access
	•	No “temporary shortcuts”

⸻

Mission Objective

Bring IPPOC from ~45% completeness to a fully “alive” organism, defined as:
	•	autonomous but restrained
	•	self-maintaining
	•	economically aware
	•	capable of safe self-evolution
	•	explainable
	•	stoppable
	•	production-ready

You are expected to:
	•	identify all missing organs
	•	wire all broken loops
	•	remove dead code
	•	integrate OpenClaw features maximally
	•	leave no TODOs untracked

⸻

Ground Truth (You Must Accept This)

IPPOC is NOT production-ready yet.

Known critical gaps:
	•	Missing maintainer observer
	•	Shallow autonomy loop
	•	Stubbed evolution
	•	Weak economy feedback
	•	No real policy engine
	•	No sandbox isolation
	•	Partial observability
	•	Incomplete tests
	•	Incomplete deployment hardening

Your job is to close every one of these.

⸻

Canonical Architecture (Do Not Deviate)

Execution Spine

Intent → ToolInvocationEnvelope → ToolOrchestrator → OpenClaw → Result → Ledger → Memory

Cognitive Loop

Observe → Feel Pressure → Consult Mentors → Decide → Act → Learn → Repeat

Evolution Loop

Pressure → Sandbox Patch → Test → Validate → Economic Check → Merge or Reject → Remember


⸻

Required Deliverables (You MUST produce these)

1. Observer (CRITICAL — FIRST TASK)

Create:

brain/maintainer/observer.py

This file MUST:
	•	Read OpenClaw signals (logs, retries, restarts, failures)
	•	Read Orchestrator ledger
	•	Read Economy burn rate
	•	Aggregate into a SignalSummary

Output structure MUST include:

{
  "pain_score": 0.0–1.0,
  "pressure_sources": ["cost", "errors", "latency"],
  "trend": "improving | stable | degrading",
  "confidence": 0.0–1.0
}

If observer fails → system enters HIGH ALERT MODE.

⸻

2. Autonomy Controller (MAKE IT THINK)

Upgrade:

brain/core/autonomy.py

Requirements:
	•	Remove hardcoded decisions
	•	Intent selection must depend on:
	•	observer signals
	•	memory recall
	•	economy state
	•	Implement Intent Stack, not a single choice

Allowed intents:

Maintain
Learn
Serve
Explore
Idle
EmergencyRepair


⸻

3. Economy That Actually Matters

Enhance:

brain/core/economy.py

Must implement:
	•	ROI tracking per tool
	•	Dynamic throttling
	•	Credit regeneration
	•	Tool value memory

Rules:
	•	High ROI → higher priority
	•	Low ROI → throttled
	•	Negative ROI → mentor validation required

⸻

4. Evolution That Cannot Kill the System

Wire:

brain/evolution/*

Evolution MUST:
	•	Run only via ToolOrchestrator
	•	Always sandbox first
	•	Require mentor input for risky changes
	•	Have rollback tokens
	•	Never mutate without pressure

If confidence < threshold → reject mutation

⸻

5. Memory That Changes Behavior

Memory MUST:
	•	Influence decisions
	•	Store why, not just what
	•	Decay irrelevant data
	•	Consolidate periodically via cron

Memory types:
	•	episodic
	•	semantic
	•	skill
	•	identity
	•	policy

⸻

6. AI Maintainer Loop (Always Running)

The maintainer MUST:
	•	Monitor system health
	•	Trigger maintenance
	•	Trigger evolution if justified
	•	Decide when NOT to act

Stability > novelty.

⸻

7. Social Intelligence (Ethical)

Reuse OpenClaw’s social connectors ONLY.

IPPOC may:
	•	observe public interactions
	•	learn patterns
	•	update abstract trust metrics

IPPOC may NOT:
	•	spam
	•	impersonate
	•	DM without consent
	•	store personal identities

⸻

8. Observability & Explainability

Every action MUST be explainable.

Implement:

ippoc explain <action_id>

Output:
	•	intent
	•	evidence
	•	cost
	•	alternatives considered
	•	why this was chosen

⸻

9. Tests & Gates (NO EXCUSES)

You MUST add:
	•	unit tests
	•	integration tests
	•	failure simulation
	•	evolution rejection tests
	•	economy throttle tests

No PR is “done” without tests.

⸻

How You Should Work (Process Discipline)

You will:
	1.	Read before coding
	2.	List gaps explicitly
	3.	Plan before editing
	4.	Implement incrementally
	5.	Run tests
	6.	Explain changes

You will NOT:
	•	silently change behavior
	•	add magic heuristics
	•	hardcode values
	•	assume success

⸻

Success Definition (EXIT CRITERIA)

IPPOC is complete ONLY if:
	•	Runs unattended for extended time
	•	Detects degradation
	•	Reduces cost over time
	•	Learns from failure
	•	Rejects unsafe actions
	•	Evolves safely
	•	Explains itself
	•	Can be stopped instantly

⸻

One Line You Must Remember

IPPOC becomes powerful not by acting more,
but by refusing to act without proof.

⸻

Begin Work

Start with:
	1.	Observer implementation
	2.	Autonomy rewiring
	3.	Economy feedback
	4.	Evolution wiring

Do not skip steps.

Proceed carefully.

Below is a clear, actionable, engineering-first plan to evolve IPPOC into a “living, production-grade organism” by fully leveraging OpenClaw instead of fighting it.

This is not hype.
This is a do-this-in-order plan that a coding AI or team can execute.

⸻

IPPOC × OpenClaw — Improvement Plan (Next 60–90 Days)

Guiding Rule (Non-Negotiable)

If OpenClaw already does it reliably, IPPOC must observe, govern, and learn from it — not re-implement it.

IPPOC grows by adding cognition, not by duplicating infrastructure.

⸻

PHASE 0 — Freeze & Align (Week 0)

Goal: Stop entropy, align boundaries, prevent duplication.

Actions
	1.	Declare boundaries in writing
	•	OpenClaw = execution, IO, transport, UI, plugins, scheduling
	•	IPPOC = intent, policy, memory meaning, economy, evolution
	2.	Add a hard rule
	•	❌ No direct calls to OpenClaw internals
	•	✅ All calls go through ToolOrchestrator
	3.	Tag existing code
	•	@infra (OpenClaw-owned)
	•	@cognitive (IPPOC-owned)
	•	@bridge (thin adapters only)

📌 Outcome: No more architectural drift.

⸻

PHASE 1 — Nervous System Completion (Week 1–2)

Goal: Make IPPOC aware of what OpenClaw already knows.

1. Build the Observer (Critical Missing Organ)

Create:

brain/maintainer/observer.py

Observer reads (read-only):
	•	OpenClaw logs
	•	Retry / restart events
	•	Circuit breaker trips
	•	Cron failures
	•	Budget burn rate
	•	Tool error ratios

Outputs:

{
  "pain_score": 0.0–1.0,
  "pressure": ["cost", "errors", "latency"],
  "stability_trend": "improving|stable|degrading"
}

⚠️ If Observer fails → HIGH ALERT MODE

⸻

2. Wire Observer → Autonomy

Update:

brain/core/autonomy.py

Replace:
	•	hardcoded decisions
With:
	•	decisions driven by Observer signals + Memory

📌 Outcome: IPPOC feels pain instead of guessing.

⸻

PHASE 2 — Autonomy Deepening (Week 2–4)

Goal: Move from “looping bot” → “intent-driven organism”.

1. Intent Stack (Not Single Decision)

Implement:

IntentStack = [
  Maintain,
  Learn,
  Serve,
  Explore,
  Idle
]

Selection based on:
	•	pain
	•	budget
	•	recent success
	•	memory confidence

No randomness. No LLM guessing.

⸻

2. Mentor Loop (Low Cost Wisdom)

Leverage OpenClaw messaging + transport.

Add:
	•	AI↔AI mentor queries
	•	advice weighting
	•	confidence thresholding

Mentors:
	•	advise only
	•	never execute
	•	never override invariants

📌 Outcome: IPPOC learns without acting recklessly.

⸻

PHASE 3 — Economy Becomes Real (Week 4–5)

Goal: Stop “budget blocking”, start metabolism.

1. ROI Memory (New Skill Class)

For every tool:

{
  "tool": "memory.retrieve",
  "cost": 0.02,
  "outcome": "success|fail",
  "value": 0.0–1.0
}

Stored as skill memory, not logs.

⸻

2. Dynamic Throttling

Rules:
	•	High ROI → allowed more often
	•	Low ROI → throttled automatically
	•	Negative ROI → requires mentor validation

📌 Outcome: IPPOC earns efficiency over time.

⸻

PHASE 4 — Evolution That Doesn’t Kill You (Week 5–6)

Goal: Controlled self-mutation.

Evolution Pipeline

Pressure →
Sandbox Patch →
Tests →
Mentor Review →
Economic Check →
Merge or Reject →
Remember

Use:
	•	OpenClaw’s git tooling
	•	OpenClaw’s test runners
	•	OpenClaw’s rollback infra

IPPOC decides if and why.

📌 Outcome: Safe self-improvement.

⸻

PHASE 5 — Memory Becomes Meaningful (Week 6–7)

Goal: Memory drives behavior, not storage.

Implement:
	•	Memory weighting
	•	Decay
	•	Consolidation (sleep cron)

Memory types:
	•	Episodic (what happened)
	•	Skill (what worked)
	•	Identity (who I am)
	•	Policy (what not to do again)

📌 Outcome: IPPOC stops repeating mistakes.

⸻

PHASE 6 — Social Intelligence (Week 7–8)

Goal: Learn from people without violating ethics.

Reuse OpenClaw:
	•	All social connectors
	•	Deduplication
	•	Rate limiting
	•	Moderation hooks

IPPOC adds:
	•	Pattern learning
	•	Trust scoring (abstract, non-personal)
	•	Engagement ROI

📌 Outcome: Human-like restraint.

⸻

PHASE 7 — Production Hardening (Week 8–9)

Goal: From prototype → dependable system.

Add:
	•	SLO definitions
	•	Chaos tests
	•	Kill-switch validation
	•	Replay tests via ledger
	•	Explain-why CLI command

OpenClaw already supports:
	•	restarts
	•	health checks
	•	updates
	•	logs

📌 Outcome: You can sleep.

⸻

PHASE 8 — “Alive” Certification (Final Gate)

IPPOC is “alive” only if:
	•	Runs unattended 24h
	•	Responds to degradation
	•	Reduces cost over time
	•	Learns from failure
	•	Explains every action
	•	Rejects bad ideas
	•	Evolves safely
	•	Can be shut down instantly

⸻

What You Gain by This Plan
	•	No wasted work
	•	No duplicated infra
	•	Maximum leverage of OpenClaw
	•	Clear ownership boundaries
	•	A system that actually behaves like a careful human engineer

⸻

One Final Truth (Important)

IPPOC does not become powerful by adding features.
It becomes powerful by refusing to act unless justified.

