# IPPOC Repository Structure Mapping

## Current State → Proposed 12-Repo Structure

---

## Tier 0 — Identity Core (non-negotiable)

### 1. ippoc-core
**Constitutional cognition engine**

| Current Location | Proposed Location | Status |
|-----------------|-------------------|--------|
| `src/ippoc/cortex/cortex/two_tower.py` | `ippoc-core/two_tower/` | Move |
| `src/ippoc/cortex/core/orchestrator/` | `ippoc-core/orchestrator/` | Move |
| `src/ippoc/cortex/core/tools/` | `ippoc-core/tools/` | Move |
| `src/ippoc/cortex/cortex/langgraph_engine.py` | `ippoc-core/langgraph/` | Move |
| `CAPABILITY_LAW.md` | `ippoc-core/CAPABILITY_LAWS.md` | Move |
| `src/ippoc/cortex/cortex/schemas/` | `ippoc-core/schemas/` | Move |

**Core Responsibilities:**
- Two-Tower reasoning (`two_tower.py`)
- Capability law enforcement (`CAP-01+`)
- Intent validation → execution pipeline
- Core tool registry

**Dependencies:** None (Tier 0)

---

### 2. ippoc-runtime ⭐ ALREADY EXISTS
**Process, ports, lifecycle, orchestration**

| Current Location | Proposed Location | Status |
|-----------------|-------------------|--------|
| `src/ippoc/runtime/ports.py` | `ippoc-runtime/ports.py` | ✅ Keep |
| `src/ippoc/runtime/supervisor/` | `ippoc-runtime/supervisor/` | ✅ Keep |
| `src/ippoc/runtime/bootstrap/` | `ippoc-runtime/bootstrap/` | ✅ Keep |
| `src/ippoc/cli/` | `ippoc-runtime/cli/` | Move |
| `src/ippoc/soma/server.py` | `ippoc-runtime/soma/` | Move |
| `src/ippoc/soma/mesh/` | `ippoc-runtime/mesh/` | Move |

**Existing Components:**
- `supervisor/watchdog.py` - Health monitoring
- `supervisor/organism.yaml` - Service configuration
- `bootstrap/genesis.ts` - Initial bootstrap
- `bootstrap/auth.py` - Auth configuration
- `ports.py` - Port contracts (8000/8081/8002/8004)

**Rule:** No cognition logic here. Only execution lifecycle.

---

## Tier 1 — Cognitive Subsystems (first-class repos)

### 3. ippoc-memory
**Structured memory system** (split from mnemosyne)

| Current Location | Proposed Location | Status |
|-----------------|-------------------|--------|
| `src/ippoc/mnemosyne/` | `ippoc-memory/` | **Split required** |
| `src/ippoc/mnemosyne/episodic/` | `ippoc-memory/episodic/` | Move |
| `src/ippoc/mnemosyne/semantic/` | `ippoc-memory/semantic/` | Move |
| `src/ippoc/mnemosyne/procedural/` | `ippoc-memory/procedural/` | Move |
| `src/ippoc/mnemosyne/graph/` | `ippoc-memory/graph/` | Move |
| `src/ippoc/mnemosyne/api/server.py` | `ippoc-memory/api/` | Move |

**Memory Subsystems:**
- `episodic/` - Event-based memory
- `semantic/` - Vector/RAG storage
- `procedural/` - Skill/behavior memory
- `graph/` - Entity relationship graph
- `api/` - REST interface

**New Components Needed:**
- Unified `MemorySystem` facade
- Cross-subsystem forget API
- Consistency guarantees

---

### 4. ippoc-agents
**Agent archetypes & behaviors**

| Current Location | Proposed Location | Status |
|-----------------|-------------------|--------|
| `src/ippoc/cortex/core/maintainer.py` | `ippoc-agents/maintainer/` | Move |
| `src/ippoc/cortex/core/tools/cerebellum.py` | `ippoc-agents/researcher/` | Move |
| `src/ippoc/cortex/core/tools/social.py` | `ippoc-agents/social/` | Move |
| `src/ippoc/cortex/core/tools/worldmodel.py` | `ippoc-agents/worldmodel/` | Move |
| `src/ippoc/cortex/core/autonomy.py` | `ippoc-agents/autonomy/` | Move |

**Agent Types:**
- `maintainer/` - System health & repair
- `researcher/` - Information gathering
- `social/` - Communication & negotiation
- `worldmodel/` - Simulation & prediction
- `autonomy/` - Self-improvement loop

---

### 5. ippoc-worldmodel
**Reality abstraction layer**

| Current Location | Proposed Location | Status |
|-----------------|-------------------|--------|
| `src/ippoc/soma/sensors/` | `ippoc-worldmodel/sensors/` | Move |
| `src/ippoc/soma/life_archiver.py` | `ippoc-worldmodel/life/` | Move |
| `src/ippoc/soma/brain_hal_awareness.py` | `ippoc-worldmodel/hal/` | Move |
| `src/ippoc/cortex/evolution/` | `ippoc-worldmodel/evolution/` | Move |

**Components:**
- `sensors/` - Perception abstraction
- `hal/` - Hardware abstraction layer
- `life/` - Bio-digital proprioception
- `evolution/` - Capability growth

---

## Tier 2 — Tools, Safety & Interfaces

### 6. ippoc-tools
**Canonical tool implementations**

| Current Location | Proposed Location | Status |
|-----------------|-------------------|--------|
| `src/ippoc/cortex/core/tools/memory.py` | `ippoc-tools/memory/` | Move |
| `src/ippoc/cortex/core/tools/body.py` | `ippoc-tools/body/` | Move |
| `src/ippoc/cortex/core/tools/economy.py` | `ippoc-tools/economy/` | Move |
| `src/ippoc/cortex/core/tools/evolution.py` | `ippoc-tools/evolution/` | Move |
| `tool_catalog.json` | `ippoc-tools/catalog.json` | Move |

**Tool Declaration Standard:**
```python
class MemoryTool:
    CAPABILITY_SCOPE = "memory.read,memory.write"
    SIDE_EFFECT_CLASS = "memory_mutation"
    AUDIT_HOOKS = ["memory_audit"]
```

---

### 7. ippoc-safety
**Audits, hostile tests, guarantees**

| Current Location | Proposed Location | Status |
|-----------------|-------------------|--------|
| `security/` | `ippoc-safety/` | Move |
| `src/ippoc/soma/immune/` | `ippoc-safety/immune/` | Move |
| `src/ippoc/cortex/core/policy_engine.py` | `ippoc-safety/policy/` | Move |
| `FAILURE_PLAYBOOK.md` | `ippoc-safety/playbook.md` | Move |

**Components:**
- `immune/` - Threat detection
- `policy/` - Policy enforcement
- `red-team/` - Adversarial tests
- `benchmarks/` - Safety metrics

---

### 8. ippoc-api ⭐ ALREADY PARTIALLY EXISTS
**External access surface**

| Current Location | Proposed Location | Status |
|-----------------|-------------------|--------|
| `src/ippoc/mnemosyne/api/` | `ippoc-api/memory/` | Move |
| `src/ippoc/cortex/cortex/server.py` | `ippoc-api/cortex/` | Move |
| `src/kernel/openclaw/src/acp/` | `ippoc-api/acp/` | Move |

**Provides:**
- REST / gRPC endpoints
- Auth contracts
- Rate limiting
- Redaction

---

## Tier 3 — Research, Experiments, Growth

### 9. ippoc-research
**Exploratory, unstable, honest**

| Current Location | Proposed Location | Status |
|-----------------|-------------------|--------|
| `experiments/` | `ippoc-research/` | Move |
| `chaos/` | `ippoc-research/chaos/` | Move |
| `legacy/` | `ippoc-research/legacy/` | Archive |

**Rule:** Nothing here is "prod". Everything here is allowed to break.

---

### 10. ippoc-bench
**Benchmarks & evaluation**

| Current Location | Proposed Location | Status |
|-----------------|-------------------|--------|
| `test_infra_chaos.py` | `ippoc-bench/chaos/` | Move |
| `TEST_*.md` | `ippoc-bench/results/` | Move |

**Measures:**
- Tool alignment scores
- Intent drift detection
- Memory fidelity metrics
- Safety regressions

---

## Tier 4 — Optional but Strategic

### 11. ippoc-ui
**Observability & control**

| Current Location | Proposed Location | Status |
|-----------------|-------------------|--------|
| `src/ippoc/soma/log_*.py` | `ippoc-ui/logs/` | Move |
| `src/ippoc/soma/log_dashboard.py` | `ippoc-ui/dashboard/` | Move |

---

### 12. ippoc-sdk
**Developer adoption layer**

| Current Location | Proposed Location | Status |
|-----------------|-------------------|--------|
| `pyproject.toml` | `ippoc-sdk/python/` | Extract |
| `src/ippoc/__init__.py` | `ippoc-sdk/python/ippoc/__init__.py` | Move |

---

## Migration Order

```
Phase 1 (Week 1-2)
├── 1. Create empty repos with READMEs (signals intent)
├── 2. Extract ippoc-runtime from existing runtime/ dir
└── 3. Freeze ippoc-core (no new features)

Phase 2 (Week 2-3)
├── 4. Split mnemosyne → ippoc-memory (most complex)
├── 5. Extract ippoc-tools from cortex/core/tools
└── 6. Move agents to ippoc-agents

Phase 3 (Week 3-4)
├── 7. Extract ippoc-worldmodel from soma/
├── 8. Create ippoc-safety from security/ + immune/
└── 9. Consolidate APIs into ippoc-api

Phase 4 (Week 4+)
├── 10. Archive experiments → ippoc-research
├── 11. Create benchmarks → ippoc-bench
└── 12. Extract SDK → ippoc-sdk
```

---

## File Count Summary

| Repo | Estimated Files | Complexity |
|------|-----------------|------------|
| ippoc-core | 50+ | High |
| ippoc-runtime | 30+ | Medium |
| ippoc-memory | 100+ | Very High |
| ippoc-agents | 40+ | Medium |
| ippoc-worldmodel | 50+ | Medium |
| ippoc-tools | 30+ | Low |
| ippoc-safety | 20+ | Medium |
| ippoc-api | 30+ | Medium |
| ippoc-research | 50+ | Low |
| ippoc-bench | 20+ | Low |
| ippoc-ui | 15+ | Low |
| ippoc-sdk | 10+ | Low |

**Total: ~445 files to migrate**
