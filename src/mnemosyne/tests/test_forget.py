import pytest
from unittest.mock import MagicMock, AsyncMock
import sys
import os
from pathlib import Path

# Add src to path
sys.path.insert(0, str(Path.cwd() / "src"))

from mnemosyne.core import MemorySystem
from mnemosyne.episodic.manager import EpisodicManager
from mnemosyne.semantic.rag import SemanticManager, SemanticObject, ContentType
from mnemosyne.procedural.manager import ProceduralManager
from mnemosyne.graph.manager import GraphManager

@pytest.mark.asyncio
async def test_forget_episodic_by_id():
    ms = MemorySystem()
    ms.episodic = MagicMock(spec=EpisodicManager)
    ms.episodic.init_db = AsyncMock()
    ms.episodic.delete = AsyncMock(return_value=1)
    ms.graph = MagicMock()
    ms.graph.init_db = AsyncMock()

    # Mock initialize to avoid side effects
    ms.initialize = AsyncMock()

    # Test
    count = await ms.forget({"id": "episodic:123"})

    assert count == 1
    ms.episodic.delete.assert_called_once_with(ids=[123])

@pytest.mark.asyncio
async def test_forget_episodic_by_type_and_time():
    ms = MemorySystem()
    ms.episodic = MagicMock(spec=EpisodicManager)
    ms.episodic.init_db = AsyncMock()
    ms.episodic.delete = AsyncMock(return_value=5)
    ms.graph = MagicMock()
    ms.graph.init_db = AsyncMock()
    ms.initialize = AsyncMock()

    # Test
    criteria = {
        "type": "episodic",
        "time_range": (None, None),
        "source": "test"
    }
    count = await ms.forget(criteria)

    assert count == 5
    ms.episodic.delete.assert_called_once_with(time_range=(None, None), source="test")

@pytest.mark.asyncio
async def test_forget_semantic_by_id():
    ms = MemorySystem()
    ms.semantic = MagicMock(spec=SemanticManager)
    ms.semantic.delete_memories = AsyncMock(return_value=True)
    ms.episodic = MagicMock()
    ms.graph = MagicMock()
    ms.initialize = AsyncMock()

    # Test
    count = await ms.forget({"ids": ["semantic:abc", "semantic:def"]})

    # Logic: calls delete_memories with ["abc", "def"]
    assert count == 2
    ms.semantic.delete_memories.assert_called_once_with(["abc", "def"])

@pytest.mark.asyncio
async def test_forget_procedural_by_name():
    ms = MemorySystem()
    ms.semantic = MagicMock()
    ms.procedural = MagicMock(spec=ProceduralManager)
    ms.procedural.unregister_skill = AsyncMock(return_value=True)
    ms.episodic = MagicMock()
    ms.graph = MagicMock()
    ms.initialize = AsyncMock()

    # Test
    count = await ms.forget({"type": "procedural", "name": "python_skill"})

    assert count == 1
    ms.procedural.unregister_skill.assert_called_once_with("python_skill")

@pytest.mark.asyncio
async def test_forget_graph_by_entity():
    ms = MemorySystem()
    ms.graph = MagicMock(spec=GraphManager)
    ms.graph.init_db = AsyncMock()
    ms.graph.delete_entity = AsyncMock(return_value=True)
    ms.episodic = MagicMock()
    ms.initialize = AsyncMock()

    # Test
    count = await ms.forget({"type": "graph", "entity": "Albert Einstein"})

    assert count == 1
    ms.graph.delete_entity.assert_called_once_with("Albert Einstein")

@pytest.mark.asyncio
async def test_semantic_manager_delete_memories():
    # Unit test for SemanticManager.delete_memories
    vector_store = MagicMock()
    vector_store.adelete = AsyncMock()

    manager = SemanticManager(vector_store, MagicMock())

    # Populate some data
    obj1 = SemanticObject(
        id="1",
        content="test",
        content_type=ContentType.TEXT,
        semantic_components=["A"],
        context_window="",
        metadata={}
    )
    manager.semantic_objects.append(obj1)
    manager.object_index["1"] = obj1
    manager.component_index["A"].append(obj1)

    # Delete
    result = await manager.delete_memories(["1"])

    assert result is True
    assert "1" not in manager.object_index
    assert len(manager.semantic_objects) == 0
    assert len(manager.component_index["A"]) == 0
    vector_store.adelete.assert_called_once_with(["1"])

@pytest.mark.asyncio
async def test_procedural_manager_unregister():
    semantic = MagicMock(spec=SemanticManager)
    semantic.delete_memories = AsyncMock()

    manager = ProceduralManager(semantic)
    manager.skill_registry["skill1"] = {"id": "obj1", "metadata": {}}

    # Unregister
    result = await manager.unregister_skill("skill1")

    assert result is True
    assert "skill1" not in manager.skill_registry
    semantic.delete_memories.assert_called_once_with(["obj1"])
