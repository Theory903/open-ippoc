import unittest
from unittest.mock import MagicMock, patch, AsyncMock
import sys
import os

# Add infra/src to path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '../../../')))

from mnemosyne.core import MemorySystem

class TestForgetFunctionality(unittest.IsolatedAsyncioTestCase):
    async def asyncSetUp(self):
        self.patcher1 = patch('mnemosyne.core.EpisodicManager')
        self.patcher2 = patch('mnemosyne.core.SemanticManager')
        self.patcher3 = patch('mnemosyne.core.ProceduralManager')
        self.patcher4 = patch('mnemosyne.core.GraphManager')

        self.MockEpisodic = self.patcher1.start()
        self.MockSemantic = self.patcher2.start()
        self.MockProcedural = self.patcher3.start()
        self.MockGraph = self.patcher4.start()

        self.episodic_instance = self.MockEpisodic.return_value
        self.semantic_instance = self.MockSemantic.return_value
        self.procedural_instance = self.MockProcedural.return_value
        self.graph_instance = self.MockGraph.return_value

        # Configure delete return values
        self.episodic_instance.delete = AsyncMock(return_value=5)
        self.semantic_instance.delete_memories = AsyncMock(return_value=3)
        self.procedural_instance.delete_skill = AsyncMock(return_value=1)
        self.graph_instance.delete_entity = AsyncMock(return_value=2)

        # Initialize MemorySystem with mocked managers
        self.memory = MemorySystem(db_url="sqlite:///:memory:", vector_store=MagicMock(), embeddings=MagicMock())

        self.memory.episodic = self.episodic_instance
        self.memory.semantic = self.semantic_instance
        self.memory.procedural = self.procedural_instance
        self.memory.graph = self.graph_instance

        # Mock initialize to prevent actual DB init attempts
        self.memory.initialize = AsyncMock(return_value=None)

    async def asyncTearDown(self):
        patch.stopall()

    async def test_forget_empty(self):
        """Verify that forget with empty criteria returns 0"""
        count = await self.memory.forget({})
        self.assertEqual(count, 0)

    async def test_forget_orchestration(self):
        """Verify that forget delegates to subsystems correctly"""
        criteria = {
            "episodic": {"source": "user", "before": "2023-01-01"},
            "semantic": {"ids": ["1", "2"]},
            "procedural": {"skill_name": "bad_skill"},
            "graph": {"entity_name": "OldEntity"}
        }

        count = await self.memory.forget(criteria)

        # Verify calls
        self.episodic_instance.delete.assert_called_with(source="user", before="2023-01-01")
        self.semantic_instance.delete_memories.assert_called_with(["1", "2"])
        self.procedural_instance.delete_skill.assert_called_with("bad_skill")
        self.graph_instance.delete_entity.assert_called_with("OldEntity")

        # Expected total: 5 (episodic) + 3 (semantic) + 1 (procedural) + 2 (graph) = 11
        self.assertEqual(count, 11)

    async def test_forget_partial(self):
        """Verify that forget works with partial criteria"""
        criteria = {
            "episodic": {"ids": [100]}
        }

        count = await self.memory.forget(criteria)

        self.episodic_instance.delete.assert_called_with(ids=[100])
        self.semantic_instance.delete_memories.assert_not_called()
        self.assertEqual(count, 5) # mocked return value

if __name__ == '__main__':
    unittest.main()
