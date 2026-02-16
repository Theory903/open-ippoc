import sys
import unittest
from unittest.mock import MagicMock, AsyncMock, patch

# Mock heavy dependencies at module level
MOCK_MODULES = [
    'langchain_core',
    'langchain_core.documents',
    'langchain_core.embeddings',
    'langchain_core.vectorstores',
    'langchain_core.prompts',
    'langchain_core.runnables',
    'langchain_community',
    'pgvector',
    'pgvector.sqlalchemy',
    'redis',
    'redis.asyncio',
    'sqlalchemy',
    'sqlalchemy.ext',
    'sqlalchemy.ext.asyncio',
    'sqlalchemy.orm',
    'sqlalchemy.dialects',
    'sqlalchemy.dialects.postgresql',
    'aiosqlite',
    'greenlet'
]

for mod_name in MOCK_MODULES:
    sys.modules[mod_name] = MagicMock()

from ippoc.mnemosyne.core import MemorySystem

class TestForgetFunctionality(unittest.IsolatedAsyncioTestCase):
    async def asyncSetUp(self):
        self.episodic_mock = AsyncMock()
        self.semantic_mock = AsyncMock()
        self.procedural_mock = AsyncMock()
        self.graph_mock = AsyncMock()

        self.patchers = [
            patch('ippoc.mnemosyne.core.EpisodicManager', return_value=self.episodic_mock),
            patch('ippoc.mnemosyne.core.GraphManager', return_value=self.graph_mock),
            patch('ippoc.mnemosyne.core.SemanticManager', return_value=self.semantic_mock),
            patch('ippoc.mnemosyne.core.ProceduralManager', return_value=self.procedural_mock)
        ]

        for p in self.patchers:
            p.start()

        self.memory = MemorySystem(
            db_url="sqlite:///:memory:",
            vector_store=MagicMock(),
            embeddings=MagicMock()
        )

        # Ensure mocks are used
        self.memory.semantic = self.semantic_mock
        self.memory.procedural = self.procedural_mock

    async def asyncTearDown(self):
        for p in self.patchers:
            p.stop()

    async def test_forget_episodic(self):
        criteria = {"episodic": {"ids": [1, 2]}}
        self.episodic_mock.delete.return_value = 2

        count = await self.memory.forget(criteria)

        self.episodic_mock.delete.assert_called_with(ids=[1, 2])
        self.assertEqual(count, 2)

    async def test_forget_semantic(self):
        criteria = {"semantic": {"ids": ["doc1", "doc2"]}}
        self.semantic_mock.delete_memories.return_value = True

        count = await self.memory.forget(criteria)

        self.semantic_mock.delete_memories.assert_called_with(["doc1", "doc2"])
        self.assertEqual(count, 2)

    async def test_forget_procedural(self):
        criteria = {"procedural": {"skills": ["python_skill", "rust_skill"]}}
        self.procedural_mock.delete_skill.side_effect = [True, True]

        count = await self.memory.forget(criteria)

        self.assertEqual(self.procedural_mock.delete_skill.call_count, 2)
        self.assertEqual(count, 2)

    async def test_forget_graph(self):
        criteria = {"graph": {"entities": ["EntityA", "EntityB"]}}
        self.graph_mock.delete_entity.side_effect = [True, False]

        count = await self.memory.forget(criteria)

        self.assertEqual(self.graph_mock.delete_entity.call_count, 2)
        self.assertEqual(count, 1)

    async def test_forget_error_handling(self):
        # Simulate exception in episodic, success in semantic
        criteria = {
            "episodic": {"ids": [1]},
            "semantic": {"ids": ["doc1"]}
        }

        self.episodic_mock.delete.side_effect = Exception("Database error")
        self.semantic_mock.delete_memories.return_value = True

        count = await self.memory.forget(criteria)

        # Should catch error and continue
        self.assertEqual(count, 1)
        self.semantic_mock.delete_memories.assert_called_with(["doc1"])

    async def test_forget_partial_failure_in_loop(self):
        criteria = {"procedural": {"skills": ["skill1", "skill2", "skill3"]}}

        # First succeeds, second fails, third succeeds
        self.procedural_mock.delete_skill.side_effect = [True, Exception("Error"), True]

        count = await self.memory.forget(criteria)

        self.assertEqual(self.procedural_mock.delete_skill.call_count, 3)
        self.assertEqual(count, 2)

if __name__ == "__main__":
    unittest.main()
