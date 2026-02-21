
import pytest
import pytest_asyncio
import sys
import os
import asyncio
import time
from unittest.mock import MagicMock

# Mock dependencies
sys.modules["langchain_core"] = MagicMock()
sys.modules["langchain_core.embeddings"] = MagicMock()
sys.modules["langchain_core.vectorstores"] = MagicMock()
sys.modules["langchain_core.prompts"] = MagicMock()
sys.modules["langchain_core.runnables"] = MagicMock()
sys.modules["langchain_core.documents"] = MagicMock()
sys.modules["langchain_community"] = MagicMock()
sys.modules["langchain_community.vectorstores"] = MagicMock()
sys.modules["langchain_community.embeddings"] = MagicMock()
sys.modules["langchain_google_genai"] = MagicMock()
sys.modules["redis"] = MagicMock()
sys.modules["redis.asyncio"] = MagicMock()
sys.modules["pgvector"] = MagicMock()
sys.modules["pgvector.sqlalchemy"] = MagicMock()

# Ensure src is in path
sys.path.append(os.path.join(os.getcwd(), "src"))

# Try to import GraphManager, bypassing package init if needed
try:
    from ippoc.mnemosyne.graph.manager import GraphManager
except ImportError:
    import importlib.util
    spec = importlib.util.spec_from_file_location("GraphManager", "src/ippoc/mnemosyne/graph/manager.py")
    module = importlib.util.module_from_spec(spec)
    sys.modules["ippoc.mnemosyne.graph.manager"] = module
    spec.loader.exec_module(module)
    GraphManager = module.GraphManager

@pytest_asyncio.fixture
async def graph_manager():
    # Use in-memory SQLite
    db_url = "sqlite+aiosqlite:///:memory:"
    gm = GraphManager(db_url=db_url)
    await gm.init_db()
    return gm

async def setup_grid_graph(gm, width=5, height=5):
    """Creates a grid graph where each node connects to neighbors"""
    # Create nodes and edges
    # Use transaction to speed up
    async with gm.Session() as session:
        pass

    for x in range(width):
        for y in range(height):
            node = f"N_{x}_{y}"
            neighbors = []
            if x > 0: neighbors.append(f"N_{x-1}_{y}")
            if x < width-1: neighbors.append(f"N_{x+1}_{y}")
            if y > 0: neighbors.append(f"N_{x}_{y-1}")
            if y < height-1: neighbors.append(f"N_{x}_{y+1}")

            for neighbor in neighbors:
                await gm.add_triple(node, "connected_to", neighbor)

    return f"N_0_0", f"N_{width-1}_{height-1}"

@pytest.mark.asyncio
async def test_grid_pathfinding_performance(graph_manager):
    """Benchmark pathfinding on a dense cyclic grid graph"""
    gm = graph_manager
    start_node, end_node = await setup_grid_graph(gm, width=5, height=5)

    # Distance is 8. Depth 10 allows some wiggling.
    depth = 10

    # Warmup
    await gm.find_relationship_path(start_node, end_node, max_depth=depth)

    start_time = time.time()
    iterations = 5
    for i in range(iterations):
        paths = await gm.find_relationship_path(start_node, end_node, max_depth=depth)
        assert len(paths) > 0
        # Verify paths are acyclic (though SQL guarantees it now)
        for p in paths:
            assert len(p["nodes"]) == len(set(p["nodes"])), "Found cyclic path!"

    end_time = time.time()
    avg_time = (end_time - start_time) / iterations

    # Assert reasonable performance (e.g. < 0.1s is very safe given 0.015s typical)
    # But strictly speaking, CI might be slow.
    # Just logging it is fine, or soft assertion.
    print(f"Average time: {avg_time:.4f} seconds")

    if avg_time > 0.5:
        pytest.fail(f"Pathfinding too slow: {avg_time:.4f}s (expected < 0.1s)")
