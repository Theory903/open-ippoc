import asyncio
import unittest
import sys
import os

# Ensure src is in path
sys.path.append(os.path.join(os.getcwd(), 'src'))

from unittest.mock import MagicMock, AsyncMock, patch
from mnemosyne.core import MemorySystem

class TestForgetRobustness(unittest.IsolatedAsyncioTestCase):
    async def asyncSetUp(self):
        # Mock dependencies
        self.mock_db_url = "sqlite+aiosqlite:///:memory:"
        self.mock_vector_store = AsyncMock()
        self.mock_vector_store.adelete = AsyncMock(return_value=True)
        self.mock_vector_store.delete = MagicMock(return_value=True)

        self.mock_embeddings = MagicMock()

        # Instantiate MemorySystem
        self.memory_system = MemorySystem(
            db_url=self.mock_db_url,
            vector_store=self.mock_vector_store,
            embeddings=self.mock_embeddings
        )

        # Mock Episodic Manager - RAISES EXCEPTION
        self.memory_system.episodic = AsyncMock()
        self.memory_system.episodic.delete.side_effect = Exception("Episodic DB Connection Failed")
        self.memory_system.episodic.init_db = AsyncMock()

        # Mock Semantic Manager - SUCCEEDS
        self.memory_system.semantic = AsyncMock()
        self.memory_system.semantic.delete_memories.return_value = True

        # Mock Procedural Manager - SUCCEEDS
        self.memory_system.procedural = AsyncMock()
        self.memory_system.procedural.delete_skill.return_value = True

        # Mock Graph Manager - RAISES EXCEPTION
        self.memory_system.graph = AsyncMock()
        self.memory_system.graph.delete_entity.side_effect = Exception("Graph DB Connection Failed")
        self.memory_system.graph.init_db = AsyncMock()

    async def test_forget_partial_failure(self):
        """Test that forget continues even if some subsystems fail"""
        criteria = {
            "episodic": {"ids": [1]},
            "semantic": {"ids": ["doc1", "doc2"]},
            "procedural": {"skills": ["test_skill"]},
            "graph": {"entities": ["TestEntity"]}
        }

        # Expect episodic to fail (0 count)
        # Expect semantic to succeed (2 count)
        # Expect procedural to succeed (1 count)
        # Expect graph to fail (0 count)
        # Total expected: 3

        count = await self.memory_system.forget(criteria)

        # Assertions
        # Verify calls were made despite failures
        self.assertTrue(self.memory_system.episodic.delete.called)
        self.assertTrue(self.memory_system.semantic.delete_memories.called)
        self.assertTrue(self.memory_system.procedural.delete_skill.called)
        self.assertTrue(self.memory_system.graph.delete_entity.called)

        print(f"Robustness test returned count: {count}")
        self.assertEqual(count, 3)

if __name__ == "__main__":
    unittest.main()
