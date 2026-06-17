import pytest
import pytest_asyncio
import sys
import os
import asyncio
from unittest.mock import MagicMock
import types
from pathlib import Path
from sqlalchemy import event, text

# Mock dependencies
def mock_package(name):
    parts = name.split('.')
    parent = None
    for i in range(1, len(parts) + 1):
        mod_name = '.'.join(parts[:i])
        if mod_name not in sys.modules:
            m = types.ModuleType(mod_name)
            sys.modules[mod_name] = m
            if parent:
                setattr(parent, parts[i-1], m)
        parent = sys.modules[mod_name]
    return parent

mock_package('langchain_core')
mock_package('langchain_core.documents')
mock_package('langchain_core.embeddings')
mock_package('langchain_core.vectorstores')
mock_package('langchain_core.prompts')
mock_package('langchain_core.output_parsers')
mock_package('langchain_core.runnables')
mock_package('langchain_community')
mock_package('langchain_community.vectorstores')
mock_package('langchain_community.embeddings')
mock_package('pgvector')
mock_package('pgvector.sqlalchemy')
mock_package('redis')
mock_package('redis.asyncio')

sys.modules['pgvector.sqlalchemy'].Vector = MagicMock()
sys.modules['redis.asyncio'].Redis = MagicMock()
sys.modules['langchain_core.documents'].Document = MagicMock()
sys.modules['langchain_core.embeddings'].Embeddings = MagicMock()
sys.modules['langchain_core.vectorstores'].VectorStore = MagicMock()
sys.modules['langchain_core.prompts'].PromptTemplate = MagicMock()
sys.modules['langchain_core.output_parsers'].StrOutputParser = MagicMock()
sys.modules['langchain_core.runnables'].RunnablePassthrough = MagicMock()
sys.modules['langchain_core.runnables'].Runnable = MagicMock()

# Ensure src is in path
sys.path.append(os.path.join(os.getcwd(), "src"))

from ippoc.mnemosyne.graph.manager import GraphManager

class QueryCounter:
    def __init__(self, engine):
        self.engine = engine
        self.count = 0
        # Attach to the underlying sync engine
        event.listen(self.engine.sync_engine, "before_cursor_execute", self.callback)

    def callback(self, conn, cursor, statement, parameters, context, executemany):
        self.count += 1

@pytest_asyncio.fixture
async def graph_manager():
    # Use in-memory SQLite
    db_url = "sqlite+aiosqlite:///:memory:"
    gm = GraphManager(db_url=db_url)
    await gm.init_db()
    return gm

@pytest.mark.asyncio
async def test_find_similar_entities_complexity(graph_manager):
    gm = graph_manager
    qc = QueryCounter(gm.engine)

    # 1. Populate Small Dataset
    # Reference Entity A -> T1
    async with gm.Session() as session:
        await session.execute(text("INSERT INTO kg_entities (name, type) VALUES ('A', 'Concept')"))
        res = await session.execute(text("SELECT id FROM kg_entities WHERE name='A'"))
        a_id = res.scalar()

        await session.execute(text("INSERT INTO kg_entities (name, type) VALUES ('T1', 'Concept')"))
        res = await session.execute(text("SELECT id FROM kg_entities WHERE name='T1'"))
        t1_id = res.scalar()

        await session.execute(text(f"INSERT INTO kg_relations (source_id, target_id, relation) VALUES ({a_id}, {t1_id}, 'rel')"))

        # Create 10 similar entities (S{i} -> T1)
        for i in range(10):
            name = f"S{i}"
            await session.execute(text(f"INSERT INTO kg_entities (name, type) VALUES ('{name}', 'Concept')"))
            res = await session.execute(text(f"SELECT id FROM kg_entities WHERE name='{name}'"))
            sid = res.scalar()
            await session.execute(text(f"INSERT INTO kg_relations (source_id, target_id, relation) VALUES ({sid}, {t1_id}, 'rel')"))

        await session.commit()

    # Run query
    qc.count = 0
    await gm.find_similar_entities("A", similarity_threshold=0.1)
    count_small = qc.count

    print(f"Queries for small dataset: {count_small}")
    # Expected:
    # 1. SELECT id FROM kg_entities WHERE name = :name
    # 2. SELECT COUNT(*) FROM kg_relations ...
    # 3. CTE Query
    assert count_small == 3

    # 2. Populate Large Dataset (add 100 more entities)
    async with gm.Session() as session:
        # Get T1 id
        res = await session.execute(text("SELECT id FROM kg_entities WHERE name='T1'"))
        t1_id = res.scalar()

        for i in range(100):
            name = f"L{i}"
            await session.execute(text(f"INSERT INTO kg_entities (name, type) VALUES ('{name}', 'Concept')"))
            res = await session.execute(text(f"SELECT id FROM kg_entities WHERE name='{name}'"))
            sid = res.scalar()
            await session.execute(text(f"INSERT INTO kg_relations (source_id, target_id, relation) VALUES ({sid}, {t1_id}, 'rel')"))
        await session.commit()

    # Run query again
    qc.count = 0
    await gm.find_similar_entities("A", similarity_threshold=0.1)
    count_large = qc.count

    print(f"Queries for large dataset: {count_large}")
    assert count_large == count_small
    assert count_large == 3
