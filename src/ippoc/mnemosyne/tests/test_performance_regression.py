import pytest
import pytest_asyncio
import sys
import os
import asyncio
from unittest.mock import MagicMock, AsyncMock, patch
from sqlalchemy.ext.asyncio import AsyncSession

# Ensure src is in path
sys.path.append(os.path.join(os.getcwd(), "src"))

from ippoc.mnemosyne.graph.manager import GraphManager

@pytest_asyncio.fixture
async def graph_manager():
    # Use in-memory SQLite
    db_url = "sqlite+aiosqlite:///:memory:"
    gm = GraphManager(db_url=db_url)
    await gm.init_db()
    return gm

@pytest.mark.asyncio
async def test_find_similar_entities_query_count(graph_manager):
    """
    Verify that find_similar_entities uses a constant number of queries
    (CTE optimization) and does NOT scale linearly with the number of entities (N+1).
    """
    gm = graph_manager

    # Setup: Create Reference Entity A and 20 Similar Entities (S0..S19)
    # A -> r -> T
    # Si -> r -> T
    await gm.add_triple("A", "r", "T")

    # Create 20 similar entities
    # If N+1 existed, query count would increase by at least 20
    for i in range(20):
        await gm.add_triple(f"S{i}", "r", "T")

    # Create 10 dissimilar entities
    for i in range(10):
        await gm.add_triple(f"D{i}", "r2", "Z")

    # Wrap the Session factory to count execute calls
    real_session_maker = gm.Session

    query_count = 0

    class SessionWrapper:
        def __init__(self, real_session):
            self.real_session = real_session

        async def __aenter__(self):
            await self.real_session.__aenter__()
            return self

        async def __aexit__(self, exc_type, exc_val, exc_tb):
            await self.real_session.__aexit__(exc_type, exc_val, exc_tb)

        async def execute(self, *args, **kwargs):
            nonlocal query_count
            query_count += 1
            return await self.real_session.execute(*args, **kwargs)

        def __getattr__(self, name):
            return getattr(self.real_session, name)

    def session_factory():
        session = real_session_maker()
        return SessionWrapper(session)

    gm.Session = session_factory

    # Run the method
    # Expected queries:
    # 1. Get ref ID (SELECT id FROM kg_entities ...)
    # 2. Get ref count (SELECT COUNT(*) ...)
    # 3. CTE query (WITH ...)
    # Total = 3

    results = await gm.find_similar_entities("A", similarity_threshold=0.0)

    # Assertions
    # Should find at least 20 similar entities (S0..S19)
    assert len(results) >= 20

    print(f"Query count: {query_count}")

    # We assert strictly < 10.
    # If it were N+1, it would be proportional to total entities (31) or similar entities (20).
    assert query_count <= 5, f"Expected O(1) queries (approx 3), got {query_count}. Potential N+1 regression detected."
