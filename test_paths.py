import sys
import os
import asyncio
from unittest.mock import MagicMock

class MockPackage(MagicMock):
    @classmethod
    def __getattr__(cls, name):
        return MagicMock()

sys.modules['langchain_core'] = MockPackage()
sys.modules['langchain_core.documents'] = MockPackage()
sys.modules['langchain_core.embeddings'] = MockPackage()
sys.modules['langchain_google_genai'] = MockPackage()
sys.modules['langchain_ollama'] = MockPackage()
sys.modules['langchain_community'] = MockPackage()
sys.modules['langchain_community.vectorstores'] = MockPackage()
sys.modules['langchain_community.embeddings'] = MockPackage()
sys.modules['langchain_community.llms'] = MockPackage()
sys.modules['langgraph'] = MockPackage()
sys.modules['langgraph.graph'] = MockPackage()
sys.modules['langgraph.prebuilt'] = MockPackage()
sys.modules['langgraph.checkpoint'] = MockPackage()
sys.modules['pgvector'] = MockPackage()
sys.modules['pgvector.sqlalchemy'] = MockPackage()
sys.modules['redis'] = MockPackage()
sys.modules['redis.asyncio'] = MockPackage()
sys.modules['pydantic_settings'] = MockPackage()
sys.modules['fastapi'] = MockPackage()
sys.modules['langchain_core.runnables'] = MockPackage()
sys.modules['langchain_core.prompts'] = MockPackage()
sys.modules['langchain_core.vectorstores'] = MockPackage()

import sqlalchemy
from sqlalchemy.ext.asyncio import AsyncSession, create_async_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy import text
import time

sys.path.insert(0, os.path.abspath('src/ippoc'))

from mnemosyne.graph.manager import GraphManager

async def test_find_path():
    manager = GraphManager(db_url="sqlite+aiosqlite:///:memory:")
    await manager.init_db()

    async with manager.Session() as session:
        # Create some entities
        await session.execute(text("INSERT INTO kg_entities (name, type) VALUES ('A', 'node')"))
        await session.execute(text("INSERT INTO kg_entities (name, type) VALUES ('B', 'node')"))
        await session.execute(text("INSERT INTO kg_entities (name, type) VALUES ('C', 'node')"))
        # Get IDs
        res = await session.execute(text("SELECT id, name FROM kg_entities"))
        nodes = {row.name: row.id for row in res}

        # Create paths A -> B -> C
        await session.execute(
            text("INSERT INTO kg_relations (source_id, target_id, relation) VALUES (:s, :t, 'to')"),
            {"s": nodes['A'], "t": nodes['B']}
        )
        await session.execute(
            text("INSERT INTO kg_relations (source_id, target_id, relation) VALUES (:s, :t, 'to')"),
            {"s": nodes['B'], "t": nodes['C']}
        )

        # Add a lot of random edges from A and B to test branching
        for i in range(100):
            await session.execute(text(f"INSERT INTO kg_entities (name, type) VALUES ('node_{i}', 'node')"))
            res2 = await session.execute(text(f"SELECT id FROM kg_entities WHERE name='node_{i}'"))
            nid = res2.scalar()
            await session.execute(
                text("INSERT INTO kg_relations (source_id, target_id, relation) VALUES (:s, :t, 'to')"),
                {"s": nodes['A'], "t": nid}
            )
            await session.execute(
                text("INSERT INTO kg_relations (source_id, target_id, relation) VALUES (:s, :t, 'to')"),
                {"s": nodes['B'], "t": nid}
            )

        await session.commit()

    # Test method
    t0 = time.time()
    paths = await manager.find_relationship_path("A", "C", max_depth=3)
    t1 = time.time()
    print("Found paths:", paths)
    print(f"Time taken: {t1-t0:.4f} seconds")

asyncio.run(test_find_path())
