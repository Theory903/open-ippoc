import pytest
import asyncio
import time
import sys
import os
from sqlalchemy import text
from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession
from sqlalchemy.orm import sessionmaker

# Ensure we can import the module
sys.path.append(os.path.join(os.getcwd(), "src"))

# Mocking heavy dependencies to avoid installing everything if possible,
# but since I installed them, I can import directly.
# However, to be safe and isolated, I'll use the installed packages.

from ippoc.mnemosyne.graph.manager import GraphManager, Base, Entity, Relation

@pytest.mark.asyncio
async def test_find_similar_entities_performance():
    """
    Performance regression test for find_similar_entities.
    Ensures that the optimized CTE implementation remains fast (avoiding N+1 queries).
    Uses the actual GraphManager class from the application.
    """
    # Use in-memory SQLite
    db_url = "sqlite+aiosqlite:///:memory:"
    gm = GraphManager(db_url=db_url)
    await gm.init_db()

    # Populate DB via direct session to control data shape
    # We can use gm.Session()
    async with gm.Session() as session:
        # 1. Populate DB with enough data to expose N+1 issues
        # Create Target Entity A
        session.add(Entity(name="A", type="Concept"))
        await session.flush()
        res = await session.execute(text("SELECT id FROM kg_entities WHERE name='A'"))
        a_id = res.scalar()

        # Create 10 relations for A
        for i in range(10):
            t_name = f"T{i}"
            session.add(Entity(name=t_name, type="Concept"))
            await session.flush()
            res = await session.execute(text(f"SELECT id FROM kg_entities WHERE name='{t_name}'"))
            t_id = res.scalar()
            session.add(Relation(source_id=a_id, target_id=t_id, relation="rel"))

        # Create 100 Similar Entities (S{i})
        for i in range(100):
            s_name = f"S{i}"
            session.add(Entity(name=s_name, type="Concept"))
            await session.flush()
            res = await session.execute(text(f"SELECT id FROM kg_entities WHERE name='{s_name}'"))
            s_id = res.scalar()

            # Shared relations
            for j in range(5):
                t_name = f"T{j}"
                res = await session.execute(text(f"SELECT id FROM kg_entities WHERE name='{t_name}'"))
                t_id = res.scalar()
                session.add(Relation(source_id=s_id, target_id=t_id, relation="rel"))

        # Create 500 Unrelated Entities (N{i}) to simulate load
        n_entities = [Entity(name=f"N{i}", type="Concept") for i in range(500)]
        session.add_all(n_entities)

        await session.commit()

        # 2. Run the actual method from GraphManager
        start_time = time.time()

        results = await gm.find_similar_entities("A", similarity_threshold=0.1)

        end_time = time.time()
        duration = end_time - start_time

        # 3. Assertions
        assert len(results) >= 100, f"Expected 100 similar entities, got {len(results)}"
        # Performance assertion: Should be very fast (< 0.1s) on in-memory DB
        # An unoptimized N+1 implementation would take significantly longer
        assert duration < 0.2, f"Query took too long: {duration:.4f}s"
