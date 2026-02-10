# ippoc-core

> Constitutional cognition engine for Intelligent Personal Processing & Orchestration Core

## Overview

`ippoc-core` is the foundational reasoning layer that enforces capability laws and orchestrates intent validation → execution. It implements the Two-Tower architecture for constitutional cognition.

## Architecture

```
                    ┌─────────────────┐
                    │   Intent        │
                    │   Validation    │
                    └────────┬────────┘
                             │
                    ┌────────▼────────┐
                    │   Two-Tower     │
                    │   Reasoning     │
                    └────────┬────────┘
                             │
                    ┌────────▼────────┐
                    │   Execution     │
                    │   Pipeline      │
                    └─────────────────┘
```

## Components

- **`two_tower/`** - Dual-model reasoning (Tower A + Tower B)
- **`orchestrator/`** - Intent dispatch and result aggregation
- **`tools/`** - Core tool registry and execution
- **`schemas/`** - Shared data structures (Signal, ActionCandidate, etc.)

## Dependencies

```
ippoc-core
├── pydantic>=2.0
├── fastapi>=0.100
└── [tools/*]
    ├── llm>=1.0
    └── [optional]
```

## Usage

```python
from ippoc_core.two_tower import TwoTowerEngine
from ippoc_core.orchestrator import Orchestrator

engine = TwoTowerEngine()
orchestrator = Orchestrator(engine)

# Execute constitutional cognition
result = await orchestrator.execute(intent)
```

## Capability Laws

All cognition must comply with `CAP-01+` capability constraints. See [CAPABILITY_LAWS.md](./CAPABILITY_LAWS.md).

## Testing

```bash
pytest tests/ -v --tb=short
```

## References

- Two-Tower Architecture: [docs/two_tower.md](./docs/two_tower.md)
- Capability Enforcement: [docs/capability_enforcement.md](./docs/capability_enforcement.md)
