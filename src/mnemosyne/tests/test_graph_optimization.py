
import pytest
import pytest_asyncio
import sys
import os
import asyncio

# Ensure src is in path
sys.path.append(os.path.join(os.getcwd(), "src"))

from mnemosyne.graph.manager import GraphManager

@pytest_asyncio.fixture
async def graph_manager():
    # Use in-memory SQLite
    db_url = "sqlite+aiosqlite:///:memory:"
    gm = GraphManager(db_url=db_url)
    await gm.init_db()
    return gm

@pytest.mark.asyncio
async def test_find_simple_path(graph_manager):
    gm = graph_manager
    await gm.add_triple("A", "connects_to", "B")
    await gm.add_triple("B", "connects_to", "C")

    paths = await gm.find_relationship_path("A", "C", max_depth=3)

    assert len(paths) >= 1
    # Check path content
    path = paths[0]
    assert path["nodes"] == ["A", "B", "C"]
    assert path["relations"] == ["connects_to", "connects_to"]

@pytest.mark.asyncio
async def test_no_path(graph_manager):
    gm = graph_manager
    await gm.add_triple("A", "connects_to", "B")
    await gm.add_triple("C", "connects_to", "D")

    paths = await gm.find_relationship_path("A", "D", max_depth=3)
    assert len(paths) == 0

@pytest.mark.asyncio
async def test_max_depth_exceeded(graph_manager):
    gm = graph_manager
    # A -> B -> C -> D
    await gm.add_triple("A", "r", "B")
    await gm.add_triple("B", "r", "C")
    await gm.add_triple("C", "r", "D")

    # Max depth 2 should not find D
    paths = await gm.find_relationship_path("A", "D", max_depth=2)
    assert len(paths) == 0

    # Max depth 3 should find D
    paths = await gm.find_relationship_path("A", "D", max_depth=3)
    assert len(paths) >= 1

@pytest.mark.asyncio
async def test_multiple_paths(graph_manager):
    gm = graph_manager
    # A -> B -> D
    # A -> C -> D
    await gm.add_triple("A", "r1", "B")
    await gm.add_triple("B", "r2", "D")
    await gm.add_triple("A", "r3", "C")
    await gm.add_triple("C", "r4", "D")

    paths = await gm.find_relationship_path("A", "D", max_depth=3)
    assert len(paths) == 2

    path_nodes = sorted([tuple(p["nodes"]) for p in paths])
    assert ("A", "B", "D") in path_nodes
    assert ("A", "C", "D") in path_nodes

@pytest.mark.asyncio
async def test_cycle_handling(graph_manager):
    gm = graph_manager
    # A <-> B
    await gm.add_triple("A", "to", "B")
    await gm.add_triple("B", "back", "A")

    # Search for path to C (not exists) shouldn't hang
    paths = await gm.find_relationship_path("A", "C", max_depth=3)
    assert len(paths) == 0

    # Search A to B should find it immediately
    paths = await gm.find_relationship_path("A", "B", max_depth=2)
    assert len(paths) >= 1
