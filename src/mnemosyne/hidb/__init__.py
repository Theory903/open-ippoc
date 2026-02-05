# __init__.py
"""
MODULE: memory.hidb

ROLE:
    The Cognitive Substrate (Vector Database).
    Abstracts PostgreSQL/pgvector and Redis into a single Memory interface.

OWNERSHIP:
    Memory subsystem.

DO NOT:
    - Lose data (Durability is key)
    - Expose SQL injection vectors

PUBLIC API:
    - semantic_search(vector) -> List[Record]
    - insert_memory(record) -> ID

ENTRYPOINTS:
    memory.hidb.client
"""
from .hidb import HiDB

__all__ = ["HiDB"]
