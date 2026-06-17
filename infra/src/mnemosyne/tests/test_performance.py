import sys
import os
from unittest.mock import MagicMock
import pytest
import asyncio
from sqlalchemy import text, event

# Mock heavy dependencies
sys.modules["langchain_core"] = MagicMock()
sys.modules["langchain_core.documents"] = MagicMock()
sys.modules["langchain_community"] = MagicMock()
sys.modules["langchain_community.vectorstores"] = MagicMock()
sys.modules["pgvector"] = MagicMock()
sys.modules["pgvector.sqlalchemy"] = MagicMock()
sys.modules["redis"] = MagicMock()
sys.modules["redis.asyncio"] = MagicMock()

# Mock internal modules to avoid import errors
sys.modules["mnemosyne.core"] = MagicMock()
sys.modules["mnemosyne.semantic"] = MagicMock()
sys.modules["mnemosyne.semantic.rag"] = MagicMock()
sys.modules["mnemosyne.episodic"] = MagicMock()
sys.modules["mnemosyne.episodic.manager"] = MagicMock()
sys.modules["mnemosyne.procedural"] = MagicMock()
sys.modules["mnemosyne.procedural.manager"] = MagicMock()
sys.modules["mnemosyne.hidb"] = MagicMock()

# Add infra/src to path
sys.path.insert(0, os.path.abspath("infra/src"))

# Import GraphManager
try:
    from mnemosyne.graph.manager import GraphManager
except ImportError:
    # Fallback if infra package structure is different in test env
    from infra.src.mnemosyne.graph.manager import GraphManager

@pytest.mark.asyncio
async def test_find_similar_entities_query_count():
    # Setup
    db_url = "sqlite+aiosqlite:///:memory:"
    gm = GraphManager(db_url=db_url)
    await gm.init_db()

    # Populate
    async with gm.Session() as session:
        # Reference Entity A
        await session.execute(text("INSERT INTO kg_entities (name, type) VALUES ('A', 'Concept')"))
        res = await session.execute(text("SELECT id FROM kg_entities WHERE name='A'"))
        a_id = res.scalar()

        # Relations for A
        for i in range(10):
            target_name = f"T{i}"
            await session.execute(text(f"INSERT INTO kg_entities (name, type) VALUES ('{target_name}', 'Concept')"))
            res = await session.execute(text(f"SELECT id FROM kg_entities WHERE name='{target_name}'"))
            t_id = res.scalar()
            await session.execute(text(f"INSERT INTO kg_relations (source_id, target_id, relation) VALUES ({a_id}, {t_id}, 'rel')"))

        # Similar Entities S0..S9 (10 entities)
        for i in range(10):
            s_name = f"S{i}"
            await session.execute(text(f"INSERT INTO kg_entities (name, type) VALUES ('{s_name}', 'Concept')"))
            res = await session.execute(text(f"SELECT id FROM kg_entities WHERE name='{s_name}'"))
            s_id = res.scalar()
            # Shared relation to T0
            res = await session.execute(text(f"SELECT id FROM kg_entities WHERE name='T0'"))
            t0_id = res.scalar()
            await session.execute(text(f"INSERT INTO kg_relations (source_id, target_id, relation) VALUES ({s_id}, {t0_id}, 'rel')"))

        # Unrelated entities (U0..U19) - 20 entities
        for i in range(20):
             u_name = f"U{i}"
             await session.execute(text(f"INSERT INTO kg_entities (name, type) VALUES ('{u_name}', 'Concept')"))

        await session.commit()

    # Count queries
    query_count = 0

    def before_cursor_execute(conn, cursor, statement, parameters, context, executemany):
        nonlocal query_count
        query_count += 1

    event.listen(gm.engine.sync_engine, "before_cursor_execute", before_cursor_execute)

    # Run
    await gm.find_similar_entities("A", similarity_threshold=0.1)

    print(f"Query count: {query_count}")

    # 3 logic queries + overhead (transaction/init).
    # Should be well below 20 (number of unrelated entities) + 10 (similar entities).
    assert query_count < 10

@pytest.mark.asyncio
async def test_find_similar_entities_limit():
    # Setup
    db_url = "sqlite+aiosqlite:///:memory:"
    gm = GraphManager(db_url=db_url)
    await gm.init_db()

    # Populate
    async with gm.Session() as session:
        # Reference Entity A
        await session.execute(text("INSERT INTO kg_entities (name, type) VALUES ('A', 'Concept')"))
        res = await session.execute(text("SELECT id FROM kg_entities WHERE name='A'"))
        a_id = res.scalar()

        # Relations for A
        # Create T0..T9
        for i in range(10):
            target_name = f"T{i}"
            await session.execute(text(f"INSERT INTO kg_entities (name, type) VALUES ('{target_name}', 'Concept')"))
            res = await session.execute(text(f"SELECT id FROM kg_entities WHERE name='{target_name}'"))
            t_id = res.scalar()
            await session.execute(text(f"INSERT INTO kg_relations (source_id, target_id, relation) VALUES ({a_id}, {t_id}, 'rel')"))

        # We need T0 ID
        res = await session.execute(text("SELECT id FROM kg_entities WHERE name='T0'"))
        t0_id = res.scalar()

        # Similar Entities S0..S19 (20 entities)
        # Each shares T0 with A
        for i in range(20):
            s_name = f"S{i}"
            await session.execute(text(f"INSERT INTO kg_entities (name, type) VALUES ('{s_name}', 'Concept')"))
            res = await session.execute(text(f"SELECT id FROM kg_entities WHERE name='{s_name}'"))
            s_id = res.scalar()
            await session.execute(text(f"INSERT INTO kg_relations (source_id, target_id, relation) VALUES ({s_id}, {t0_id}, 'rel')"))

        await session.commit()

    # Default limit is 50, we have 20 results. Should get 20.
    results = await gm.find_similar_entities("A", similarity_threshold=0.0)
    assert len(results) == 20

    # Custom limit 5. Should get 5.
    results = await gm.find_similar_entities("A", similarity_threshold=0.0, limit=5)
    assert len(results) == 5

if __name__ == "__main__":
    asyncio.run(test_find_similar_entities_query_count())
    asyncio.run(test_find_similar_entities_limit())
