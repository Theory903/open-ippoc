
import pytest
import pytest_asyncio
import sys
import os
import asyncio

# Ensure src is in path
sys.path.append(os.path.join(os.getcwd(), "src"))

# Mock heavy dependencies to avoid import errors
from unittest.mock import MagicMock
import types

m = types.ModuleType("langchain_core")
sys.modules["langchain_core"] = m
m.documents = types.ModuleType("langchain_core.documents")
m.documents.Document = MagicMock()
sys.modules["langchain_core.documents"] = m.documents
m.embeddings = types.ModuleType("langchain_core.embeddings")
m.embeddings.Embeddings = MagicMock()
sys.modules["langchain_core.embeddings"] = m.embeddings
m.vectorstores = types.ModuleType("langchain_core.vectorstores")
m.vectorstores.VectorStore = MagicMock()
sys.modules["langchain_core.vectorstores"] = m.vectorstores
m.prompts = types.ModuleType("langchain_core.prompts")
m.prompts.PromptTemplate = MagicMock()
sys.modules["langchain_core.prompts"] = m.prompts
m.runnables = types.ModuleType("langchain_core.runnables")
m.runnables.Runnable = MagicMock()
sys.modules["langchain_core.runnables"] = m.runnables
m.output_parsers = types.ModuleType("langchain_core.output_parsers")
sys.modules["langchain_core.output_parsers"] = m.output_parsers
m.language_models = types.ModuleType("langchain_core.language_models")
sys.modules["langchain_core.language_models"] = m.language_models

m_comm = types.ModuleType("langchain_community")
sys.modules["langchain_community"] = m_comm
m_comm.vectorstores = types.ModuleType("langchain_community.vectorstores")
sys.modules["langchain_community.vectorstores"] = m_comm.vectorstores
m_comm.embeddings = types.ModuleType("langchain_community.embeddings")
sys.modules["langchain_community.embeddings"] = m_comm.embeddings

sys.modules["pgvector"] = MagicMock()
sys.modules["pgvector.sqlalchemy"] = MagicMock()

sys.modules["redis"] = MagicMock()
sys.modules["redis.asyncio"] = MagicMock()

# We need to import GraphManager directly to bypass package __init__ if possible,
# or just rely on mocks if we import via package.
# But importing via package 'from ippoc.mnemosyne.graph.manager' triggers ippoc.mnemosyne.__init__
# which imports core -> semantic -> rag -> langchain.
# So mocks must be in place before that import.

from ippoc.mnemosyne.graph.manager import GraphManager

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

@pytest.mark.asyncio
async def test_find_similar_entities(graph_manager):
    gm = graph_manager
    # Ref Entity: A
    # A -> B (r1)
    # A -> C (r2)
    await gm.add_triple("A", "r1", "B")
    await gm.add_triple("A", "r2", "C")

    # Similar Entity: D
    # D -> B (r1)  <-- Match
    # D -> E (r3)
    await gm.add_triple("D", "r1", "B")
    await gm.add_triple("D", "r3", "E")

    # Dissimilar Entity: F
    # F -> G (r4)
    await gm.add_triple("F", "r4", "G")

    # Find similar to A
    # Intersection(A, D) = 1 (r1->B)
    # Union(A, D) = 2 (A) + 2 (D) - 1 = 3
    # Sim = 1/3 = 0.333...

    similar = await gm.find_similar_entities("A", similarity_threshold=0.1)

    # F should not be in results because intersection is 0
    # D should be in results

    assert len(similar) == 1
    assert similar[0]["entity"] == "D"
    assert abs(similar[0]["similarity"] - (1/3)) < 0.01
    assert similar[0]["shared_relations"] == 1
