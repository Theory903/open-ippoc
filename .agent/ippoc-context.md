# IPPOC Architecture Context

## What is IPPOC?

IPPOC (Intelligent Personal Processing & Orchestration Core) is a sovereign cognitive architecture that powers OpenClaw. It's a "brain" with two main components:

## Architecture: Two-Tower Design

### Tower A — Impulse/Intuition
- **Speed:** Fast, continuous, always running
- **Cost:** Cheap (uses local Ollama models like kimi-k2.5)
- **Role:** Proposes ideas, generates hypotheses, creates inner monologue, drafts code, asks questions
- **Vibe:** "What should I try next?" — exploratory, can be wrong

### Tower B — Validation/Reasoning  
- **Speed:** Slow, deliberate, triggered selectively
- **Cost:** Expensive (uses large models)
- **Role:** Validates proposals, catches errors, approves risky actions, evaluates economic decisions
- **Vibe:** "Is this correct?" — critical, authoritative

### The Interaction Rule
**Tower A proposes → Tower B approves or rejects**

Tower B only steps in when:
- Cost exceeds threshold
- System invariants are involved
- Evolution or self-mutation is happening

## Three Pillars of IPPOC

### 1. Cognition (Brain/Mind)
- Tower A (Impulse/Intuition): Fast, cheap, local models generating hypotheses
- Tower B (Validation/Reasoning): Slow, expensive, large models approving risky actions
- LangGraph-based reasoning engine for continuous thought loops

### 2. Memory (HiDB — Hippocampus-Inspired Database)
- Episodic: Event-based experiences
- Semantic: Knowledge and facts with embeddings
- Procedural: Skills and tool execution patterns
- Implements "Solid Hybrid RAG" for persistent cognitive state

### 3. Economy (Resource Management)
- Budget-capped operations with IPPC (IPPOC Points/Credits)
- Cost-aware decision making — "Money feeds intelligence, intelligence never worships money"
- ROI-based evolution decisions and swarm resource allocation

## Services

IPPOC runs two services:
- **Soma (port 8081):** Identity, auth, and core services
- **Cortex (port 8000):** Cognitive processing, tool execution

## Access Points
- Soma Health: http://localhost:8081/v1/system/diagnostics
- Cortex Health: http://localhost:8000/healthz
- IPPOC Status: `IPPOC_ENABLED=true pnpm ippoc status`

## Communication
OpenClaw connects to IPPOC via the `IPPOC_ENABLED=true` environment variable, which enables the IPPOC plugin that integrates cognitive tools and memory access.
