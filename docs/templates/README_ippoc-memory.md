# ippoc-memory

> Structured memory system for IPPOC — episodic, semantic, procedural, and graph storage

## Overview

`ippoc-memory` provides unified long-term memory for IPPOC with four specialized subsystems:

1. **Episodic** — Event-based temporal memories
2. **Semantic** — Vector-based knowledge with RAG
3. **Procedural** — Skill and behavior memory
4. **Graph** — Entity relationship knowledge graph

## Architecture

```
┌────────────────────────────────────────────────────────┐
│                   MemorySystem                          │
│  ┌─────────┬────────────┬──────────┬──────────────┐  │
│  │Episodic │ Semantic   │Procedural│ Graph        │  │
│  │Manager  │ Manager    │Manager   │ Manager      │  │
│  └────┬────┴─────┬──────┴────┬─────┴──────┬───────┘  │
│       │          │           │            │           │
│       └──────────┴───────────┴────────────┘           │
│                        │                              │
│              ┌─────────▼─────────┐                     │
│              │   Forget API     │                     │
│              │   (Unified)      │                     │
│              └──────────────────┘                     │
└────────────────────────────────────────────────────────┘
```

## Subsystems

### Episodic Manager
Stores event-based memories with temporal context.

```python
await episodic.store(
    event="user.login",
    timestamp=datetime.utcnow(),
    metadata={"ip": "192.168.1.1"}
)
```

### Semantic Manager
Vector-based storage with RAG capabilities.

```python
from ippoc_memory.semantic import SemanticManager

semantic = SemanticManager()
await semantic.add_documents(
    texts=["Knowledge piece 1", "Knowledge piece 2"],
    embeddings=embeddings
)
```

### Procedural Manager
Skill and behavior memory.

```python
await procedural.record_skill(
    skill_id="file_write",
    code_hash="abc123",
    success_rate=0.95
)
```

### Graph Manager
Entity-relationship knowledge graph.

```python
graph = GraphManager()
await graph.add_entity(
    id="person:alice",
    type="Person",
    properties={"name": "Alice"}
)
await graph.add_relation(
    source="person:alice",
    relation="knows",
    target="person:bob"
)
```

## Unified API

### Store Memory
```python
from ippoc_memory import MemorySystem

memory = MemorySystem()
await memory.store(
    type="episodic",
    content={"event": "user.message", "text": "Hello"}
)
```

### Retrieve Memories
```python
memories = await memory.retrieve(
    query="recent user messages",
    limit=10
)
```

### Forget (Delete)
```python
# Forget by criteria
count = await memory.forget(
    criteria={
        "episodic": {"before": datetime(2024, 1, 1)},
        "semantic": {"ids": ["doc123"]},
        "procedural": {"skill_id": "unused_skill"},
        "graph": {"entity_id": "obsolete_entity"}
    }
)
```

## Installation

```bash
pip install ippoc-memory
```

## Dependencies

```
ippoc-memory
├── pydantic>=2.0
├── langchain>=0.1.0
├── langchain-google-genai>=0.0.6
├── psycopg2-binary  # For PGVector
└── [all]
    ippoc-core>=0.9.0
```

## Configuration

```yaml
memory:
  episodic:
    backend: sqlite
    path: ~/.ippoc/memory/episodic.db
    
  semantic:
    backend: pgvector
    connection: postgresql://user:pass@localhost:5432/ippoc
    collection: hippocampus_v2
    
  procedural:
    backend: sqlite
    path: ~/.ippoc/memory/procedural.db
    
  graph:
    backend: sqlite
    path: ~/.ippoc/memory/graph.db
```

## Testing

```bash
pytest tests/ -v --tb=short -k "not pgvector"
```

## Performance

- **Episodic**: ~10K events/second (SQLite)
- **Semantic**: ~1K docs/second (PGVector)
- **Graph**: ~5K entities/second (SQLite)
- **Forget**: O(n) across all subsystems

## References

- API Documentation: [docs/api.md](./docs/api.md)
- Schema Definitions: [docs/schemas.md](./docs/schemas.md)
- Forget Functionality: [docs/forget.md](./docs/forget.md)
