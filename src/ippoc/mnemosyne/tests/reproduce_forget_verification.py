import asyncio
import sys
import os
from unittest.mock import AsyncMock, MagicMock

# Ensure we can import from src/ippoc
sys.path.append(os.path.join(os.getcwd(), 'src/ippoc'))

from mnemosyne.core import MemorySystem

async def main():
    print("Starting reproduction of forget functionality...")

    # Initialize MemorySystem with dummy args
    mock_vector_store = MagicMock()
    mock_embeddings = MagicMock()

    # Use in-memory sqlite for base
    ms = MemorySystem(
        db_url="sqlite+aiosqlite:///:memory:",
        vector_store=mock_vector_store,
        embeddings=mock_embeddings
    )

    # Mock the managers directly to verify orchestration
    ms.episodic = AsyncMock()
    ms.episodic.delete.return_value = 5  # simulate 5 episodic memories deleted

    ms.semantic = AsyncMock()
    ms.semantic.delete_memories.return_value = True # successful deletion

    ms.procedural = AsyncMock()
    ms.procedural.delete_skill.return_value = True # successful deletion

    ms.graph = AsyncMock()
    ms.graph.delete_entity.return_value = True # successful deletion

    # Define criteria
    criteria = {
        "episodic": {"ids": [1, 2, 3, 4, 5]},
        "semantic": {"ids": ["doc1", "doc2", "doc3"]},
        "procedural": {"skills": ["skillA"]},
        "graph": {"entities": ["Entity1", "Entity2"]}
    }

    print(f"Calling forget with criteria: {criteria}")
    count = await ms.forget(criteria)

    print(f"Total deleted count returned: {count}")

    # Verify calls
    assert ms.episodic.delete.called, "Episodic delete not called"
    ms.episodic.delete.assert_called_with(ids=[1, 2, 3, 4, 5])
    print("Episodic delete called correctly.")

    assert ms.semantic.delete_memories.called, "Semantic delete not called"
    ms.semantic.delete_memories.assert_called_with(["doc1", "doc2", "doc3"])
    print("Semantic delete called correctly.")

    assert ms.procedural.delete_skill.called, "Procedural delete not called"
    ms.procedural.delete_skill.assert_called_with("skillA")
    print("Procedural delete called correctly.")

    assert ms.graph.delete_entity.called, "Graph delete not called"
    # graph.delete_entity is called per entity in loop
    assert ms.graph.delete_entity.call_count == 2
    ms.graph.delete_entity.assert_any_call("Entity1")
    ms.graph.delete_entity.assert_any_call("Entity2")
    print("Graph delete called correctly.")

    # Expected count:
    # Episodic: 5
    # Semantic: len(["doc1", "doc2", "doc3"]) = 3
    # Procedural: 1 skill * 1 = 1
    # Graph: 2 entities * 1 = 2
    expected_count = 5 + 3 + 1 + 2 # 11

    if count == expected_count:
        print(f"SUCCESS: Count matches expected value ({expected_count}).")
    else:
        print(f"FAILURE: Count mismatch. Expected {expected_count}, got {count}")
        sys.exit(1)

if __name__ == "__main__":
    asyncio.run(main())
