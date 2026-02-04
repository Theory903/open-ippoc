# HIDB Cognitive Architecture

**Layer:** System / Macro
**Date:** 2026-01-23

---

## 1. Macro View
```text
┌────────────────────────────────────────────┐
│                CORTEX (LLM)                │
│                                            │
│  - Reasoning, Language, Planning           │
│  - Salience Assignment                     │
└───────────────┬────────────────────────────┘
                │  HippocampusPort (Airlock)
                ▼
┌────────────────────────────────────────────┐
│            HIPPOCAMPUS (HIDB)              │
│         Persistent Cognitive Memory        │
└────────────────────────────────────────────┘
```

## 2. Internal Brain Structure (HIDB Core)
```text
┌─────────────────────────────────────────────────────────┐
│                     HIDB ENGINE                         │
│                                                         │
│  ┌───────────────┐    ┌─────────────────────────────┐   │
│  │  TextEncoder  │───▶│  CognitivePacket (Vector)   │   │
│  └───────────────┘    └──────────────┬──────────────┘   │
│                                      │                  │
│                                      ▼                  │
│  ┌──────────────────────────────────────────────────┐   │
│  │              NEURAL LATTICE (LSH)                │   │
│  │  Fast candidate lookup (semantic proximity)      │   │
│  └──────────────┬───────────────────────────────────┘   │
│                 │                                       │
│                 ▼                                       │
│  ┌──────────────────────────────────────────────────┐   │
│  │            NEURON STORE (SoA, mmap)              │   │
│  │                                                  │   │
│  │  Neuron:                                         │   │
│  │   - embedding[256], salience, confidence         │   │
│  │   - age / last_fired                             │   │
│  │   - flags (META, STABLE, etc.)                   │   │
│  └──────────────────────────────────────────────────┘   │
└─────────────────────────────────────────────────────────┘
```

## 3. Dynamic Loops

### Memory Lifecycle
```text
INPUT -> Encode -> Match?
   YES -> Reinforce / Habituate
   NO  -> Neurogenesis (Spawn)
   HIGH SALIENCE -> Replay Buffer
```

### Sleep & Reflection
```text
SLEEP MODE
  -> Replay Buffer -> Consolidation
  -> Pruning (Decay)
  -> REFLECTION:
       Observe -> Cluster -> Spawn META-NEURON (Belief)
```

## 4. Meta-Neurons (Beliefs)
Represent Concepts, Themes, Habits, Beliefs.
*   High stability, Slow decay.
*   Participate in queries like normal memory.

## 5. Query Path
```text
Query Vector -> LSH Candidates -> Exact Similarity -> QueryResult
```
