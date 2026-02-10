import asyncio
import sys
import os
import pytest
import pytest_asyncio
from pathlib import Path

# Add infra/src to python path
# infra/src/mnemosyne/tests -> ../.. -> infra/src
sys.path.insert(0, str(Path(__file__).parent.parent.parent))

try:
    from mnemosyne.graph.manager import GraphManager
except ImportError:
    # Try again with one less level if executed from root or weird context
    sys.path.insert(0, str(Path(__file__).parent.parent))
    from mnemosyne.graph.manager import GraphManager

@pytest_asyncio.fixture
async def graph_manager():
    # Use in-memory SQLite
    db_url = "sqlite+aiosqlite:///:memory:"
    gm = GraphManager(db_url=db_url)
    await gm.init_db()
    return gm

@pytest.mark.asyncio
async def test_similarity_basic(graph_manager):
    gm = graph_manager
    # A -> r1 -> B
    # C -> r1 -> B
    # A and C share (r1, B) relation. They should be similar.

    await gm.add_triple("A", "r1", "B")
    await gm.add_triple("C", "r1", "B")

    # A has 1 relation. C has 1 relation. Intersection is 1. Union is 1.
    # Similarity should be 1.0

    similar = await gm.find_similar_entities("A", similarity_threshold=0.0)
    assert len(similar) == 1
    assert similar[0]["entity"] == "C"
    assert similar[0]["similarity"] == 1.0

@pytest.mark.asyncio
async def test_similarity_partial(graph_manager):
    gm = graph_manager
    # A -> r1 -> X
    # A -> r2 -> Y

    # B -> r1 -> X (shared)
    # B -> r3 -> Z

    await gm.add_triple("A", "r1", "X")
    await gm.add_triple("A", "r2", "Y")

    await gm.add_triple("B", "r1", "X")
    await gm.add_triple("B", "r3", "Z")

    # A relations: {(r1, X), (r2, Y)} (size 2)
    # B relations: {(r1, X), (r3, Z)} (size 2)
    # Intersection: {(r1, X)} (size 1)
    # Union: 3
    # Similarity: 1/3 = 0.333

    similar = await gm.find_similar_entities("A", similarity_threshold=0.0)
    assert len(similar) == 1
    assert similar[0]["entity"] == "B"
    assert abs(similar[0]["similarity"] - 0.333) < 0.01

@pytest.mark.asyncio
async def test_similarity_no_match(graph_manager):
    gm = graph_manager
    # A -> r1 -> X
    # B -> r2 -> Y

    await gm.add_triple("A", "r1", "X")
    await gm.add_triple("B", "r2", "Y")

    similar = await gm.find_similar_entities("A", similarity_threshold=0.0)

    # Should find B with similarity 0.0
    found_b = False
    for s in similar:
        if s["entity"] == "B":
            found_b = True
            assert s["similarity"] == 0.0

    assert found_b
