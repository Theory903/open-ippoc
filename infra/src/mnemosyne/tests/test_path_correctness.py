import asyncio
import sys
import os
import pytest
import pytest_asyncio
from pathlib import Path
from sqlalchemy import text

# Add infra/src to python path
sys.path.insert(0, str(Path(__file__).parent.parent.parent))

try:
    from mnemosyne.graph.manager import GraphManager
except ImportError:
    sys.path.insert(0, str(Path(__file__).parent.parent))
    from mnemosyne.graph.manager import GraphManager

@pytest_asyncio.fixture
async def graph_manager():
    db_url = "sqlite+aiosqlite:///:memory:"
    gm = GraphManager(db_url=db_url)
    await gm.init_db()
    return gm

@pytest.mark.asyncio
async def test_path_finding_simple(graph_manager):
    gm = graph_manager
    # A -> B -> C
    await gm.add_triple("A", "rel", "B")
    await gm.add_triple("B", "rel", "C")

    paths = await gm.find_relationship_path("A", "C", max_depth=3)
    assert len(paths) == 1
    assert paths[0]["nodes"] == ["A", "B", "C"]

@pytest.mark.asyncio
async def test_path_finding_cycle_avoidance(graph_manager):
    gm = graph_manager
    # A -> B -> A (cycle)
    # A -> C -> D
    await gm.add_triple("A", "to", "B")
    await gm.add_triple("B", "to", "A")
    await gm.add_triple("A", "to", "C")
    await gm.add_triple("C", "to", "D")

    # Path A -> D should be found
    paths = await gm.find_relationship_path("A", "D", max_depth=4)
    assert len(paths) >= 1
    found = False
    for p in paths:
        if p["nodes"] == ["A", "C", "D"]:
            found = True
            break
    assert found

    # Path A -> B -> A -> C -> D should NOT be found (cycle)
    for p in paths:
        nodes = p["nodes"]
        # Check for duplicates in path
        assert len(nodes) == len(set(nodes)), f"Cycle found in path: {nodes}"

@pytest.mark.asyncio
async def test_path_finding_diamond(graph_manager):
    gm = graph_manager
    # A -> B -> D
    # A -> C -> D
    await gm.add_triple("A", "to", "B")
    await gm.add_triple("B", "to", "D")
    await gm.add_triple("A", "to", "C")
    await gm.add_triple("C", "to", "D")

    paths = await gm.find_relationship_path("A", "D", max_depth=3)
    assert len(paths) == 2
    path_strs = sorted([",".join(p["nodes"]) for p in paths])
    assert path_strs == ["A,B,D", "A,C,D"]
