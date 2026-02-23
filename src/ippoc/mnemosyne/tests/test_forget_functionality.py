import asyncio
import unittest
import sys
import os

# Ensure src is in path
sys.path.append(os.path.join(os.getcwd(), 'src'))

from unittest.mock import MagicMock, AsyncMock, patch
from mnemosyne.core import MemorySystem

class TestForgetFunctionality(unittest.IsolatedAsyncioTestCase):
    async def asyncSetUp(self):
        # Mock dependencies
        self.mock_db_url = "sqlite+aiosqlite:///:memory:"
        self.mock_vector_store = AsyncMock()
        # Mock delete and adelete on vector store
        self.mock_vector_store.adelete = AsyncMock(return_value=True)
        self.mock_vector_store.delete = MagicMock(return_value=True)

        self.mock_embeddings = MagicMock()

        # Instantiate MemorySystem
        self.memory_system = MemorySystem(
            db_url=self.mock_db_url,
            vector_store=self.mock_vector_store,
            embeddings=self.mock_embeddings
        )

        # Mock Episodic Engine and Session
        self.mock_episodic_engine = AsyncMock()
        # Ensure begin is MagicMock (sync function returning async context manager)
        self.mock_episodic_engine.begin = MagicMock()

        mock_conn = AsyncMock()
        mock_cm = MagicMock()
        mock_cm.__aenter__ = AsyncMock(return_value=mock_conn)
        mock_cm.__aexit__ = AsyncMock(return_value=None)
        self.mock_episodic_engine.begin.return_value = mock_cm

        self.memory_system.episodic._engine = self.mock_episodic_engine

        self.mock_episodic_session = AsyncMock()
        # Mock result for delete
        mock_result = MagicMock()
        mock_result.rowcount = 5
        self.mock_episodic_session.execute.return_value = mock_result
        # sessionmaker is sync, returns session which is async context manager?
        # self.async_session() call.
        self.memory_system.episodic._async_session = MagicMock(return_value=self.mock_episodic_session)
        self.mock_episodic_session.__aenter__.return_value = self.mock_episodic_session
        self.mock_episodic_session.__aexit__.return_value = None

        # Mock Graph Engine and Session
        self.mock_graph_engine = AsyncMock()
        self.mock_graph_engine.begin = MagicMock()

        mock_conn_graph = AsyncMock()
        mock_cm_graph = MagicMock()
        mock_cm_graph.__aenter__ = AsyncMock(return_value=mock_conn_graph)
        mock_cm_graph.__aexit__ = AsyncMock(return_value=None)
        self.mock_graph_engine.begin.return_value = mock_cm_graph
        self.memory_system.graph.engine = self.mock_graph_engine

        self.mock_graph_session = AsyncMock()
        self.mock_graph_session.__aenter__.return_value = self.mock_graph_session
        self.mock_graph_session.__aexit__.return_value = None

        # Mock result for select (fetchone) and delete
        mock_select_result = MagicMock()
        mock_select_result.fetchone.return_value = [1] # entity id

        async def graph_execute_side_effect(*args, **kwargs):
            query = str(args[0])
            if "SELECT id FROM kg_entities" in query:
                return mock_select_result
            else:
                return MagicMock()

        self.mock_graph_session.execute.side_effect = graph_execute_side_effect
        self.memory_system.graph.Session = MagicMock(return_value=self.mock_graph_session)

        # Mock Procedural Registry
        self.memory_system.procedural.skill_registry = {
            "test_skill": {"id": "skill_doc_1", "metadata": {}}
        }

        # Mock Semantic Objects and Index
        from mnemosyne.semantic.rag import SemanticObject, ContentType
        doc1 = SemanticObject(
            id="doc1",
            content="c1",
            content_type=ContentType.TEXT,
            semantic_components=["comp1"],
            context_window="",
            metadata={}
        )
        doc2 = SemanticObject(
            id="doc2",
            content="c2",
            content_type=ContentType.TEXT,
            semantic_components=["comp2"],
            context_window="",
            metadata={}
        )
        self.memory_system.semantic.object_index = {"doc1": doc1, "doc2": doc2}
        self.memory_system.semantic.semantic_objects = [doc1, doc2]

        # Ensure component_index is initialized (testing __init__)
        from collections import defaultdict
        self.assertIsInstance(self.memory_system.semantic.component_index, defaultdict)

        # Populate component_index
        self.memory_system.semantic.component_index["comp1"].append(doc1)
        self.memory_system.semantic.component_index["comp2"].append(doc2)

    async def test_forget_success(self):
        criteria = {
            "episodic": {"ids": [1, 2]},
            "semantic": {"ids": ["doc1", "doc2"]},
            "procedural": {"skills": ["test_skill"]},
            "graph": {"entities": ["TestEntity"]}
        }

        count = await self.memory_system.forget(criteria)

        # Assertions
        # Episodic
        self.assertTrue(self.mock_episodic_session.execute.called)

        # Semantic
        self.assertTrue(self.mock_vector_store.adelete.called)

        # Procedural
        self.assertNotIn("test_skill", self.memory_system.procedural.skill_registry)

        # Graph
        self.assertTrue(self.mock_graph_session.execute.call_count >= 2)

        print(f"Forget returned count: {count}")
        self.assertEqual(count, 9)

if __name__ == "__main__":
    unittest.main()
