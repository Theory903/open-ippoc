import asyncio
import unittest
import sys
import os
from unittest.mock import MagicMock, AsyncMock

# Ensure src is in path to import ippoc
sys.path.append(os.path.join(os.getcwd(), 'src'))

# MOCKING STRATEGY:
# Mock ONLY libraries that are missing or heavy.
# Use REAL sqlalchemy/aiosqlite.

# LangChain
sys.modules['langchain_core'] = MagicMock()
sys.modules['langchain_core.documents'] = MagicMock()
sys.modules['langchain_core.embeddings'] = MagicMock()
sys.modules['langchain_core.vectorstores'] = MagicMock()
sys.modules['langchain_core.prompts'] = MagicMock()
sys.modules['langchain_core.runnables'] = MagicMock()
sys.modules['langchain_community'] = MagicMock()

# pgvector
sys.modules['pgvector'] = MagicMock()
sys.modules['pgvector.sqlalchemy'] = MagicMock()

# Redis
redis_mock = MagicMock()
sys.modules['redis'] = redis_mock
sys.modules['redis.asyncio'] = redis_mock

# Others
sys.modules['pytesseract'] = MagicMock()
sys.modules['PIL'] = MagicMock()

# Now import the module under test
try:
    from ippoc.mnemosyne.core import MemorySystem, MemoryFragment
    # Also import managers to inspect/populate data
    from ippoc.mnemosyne.episodic.manager import EpisodicEvent
    from ippoc.mnemosyne.graph.manager import Entity, Relation
except ImportError as e:
    print(f"Import failed: {e}")
    raise

class TestForgetIntegration(unittest.IsolatedAsyncioTestCase):
    async def asyncSetUp(self):
        # Use in-memory SQLite
        self.db_url = "sqlite+aiosqlite:///:memory:"

        # Mock vector store for Semantic/Procedural
        self.mock_vector_store = AsyncMock()
        self.mock_vector_store.adelete = AsyncMock(return_value=True) # SemanticManager uses adelete if available
        # Also need delete just in case
        self.mock_vector_store.delete = MagicMock(return_value=True)
        # Mock aadd_documents (add_memory calls this)
        self.mock_vector_store.aadd_documents = AsyncMock(return_value=["doc1", "doc2"])

        # Mock embeddings
        self.mock_embeddings = MagicMock()

        # Instantiate MemorySystem with REAL DB but Mocked VectorStore
        self.memory_system = MemorySystem(
            db_url=self.db_url,
            vector_store=self.mock_vector_store,
            embeddings=self.mock_embeddings
        )

        # Initialize DB (creates tables)
        await self.memory_system.initialize()

        # Populate Episodic Data
        async with self.memory_system.episodic.async_session() as session:
            session.add(EpisodicEvent(id=1, content="Event 1", source="test", modality="text", metadata_={"tag": "A"}))
            session.add(EpisodicEvent(id=2, content="Event 2", source="test", modality="text", metadata_={"tag": "B"}))
            session.add(EpisodicEvent(id=3, content="Event 3", source="other", modality="text", metadata_={"tag": "C"}))
            await session.commit()

        # Populate Graph Data
        # Add entity "TestEntity" and some relations
        # Since we use real GraphManager, we can use add_triple or direct DB access
        await self.memory_system.graph.add_triple("TestEntity", "related_to", "OtherEntity")
        await self.memory_system.graph.add_triple("OtherEntity", "related_to", "ThirdEntity")

        # Populate Procedural Registry (Mocked logic inside ProceduralManager uses registry)
        # ProceduralManager registers skill in memory registry AND calls semantic.add_memory.
        # We can just inject into registry.
        self.memory_system.procedural.skill_registry["test_skill"] = {
            "id": "skill_doc_1",
            "metadata": {"skill_name": "test_skill"}
        }

    async def test_forget_real_db(self):
        criteria = {
            "episodic": {"ids": [1, 2]}, # Delete ID 1 and 2
            "semantic": {"ids": ["doc1"]}, # Mocked
            "procedural": {"skills": ["test_skill"]}, # Should remove from registry
            "graph": {"entities": ["TestEntity"]} # Should remove TestEntity and its relations
        }

        # Run forget
        count = await self.memory_system.forget(criteria)

        print(f"Forget returned count: {count}")

        # Verification

        # 1. Episodic: Should have deleted 2 events. Event 3 should remain.
        async with self.memory_system.episodic.async_session() as session:
            # Check count
            from sqlalchemy import select, func
            result = await session.execute(select(func.count(EpisodicEvent.id)))
            remaining_count = result.scalar()
            self.assertEqual(remaining_count, 1, "Should have 1 episodic event remaining")

            # Check remaining event is ID 3
            result = await session.execute(select(EpisodicEvent.id))
            remaining_ids = result.scalars().all()
            self.assertEqual(remaining_ids, [3])

        # 2. Semantic: Mocked, verify call
        # SemanticManager calls delete_memories(['doc1']) -> vector_store.adelete(['doc1'])
        # Since we mocked adelete to return True, it should count as 1.
        self.mock_vector_store.adelete.assert_called()

        # 3. Procedural: Should remove from registry
        self.assertNotIn("test_skill", self.memory_system.procedural.skill_registry)

        # 4. Graph: TestEntity should be gone. OtherEntity should remain.
        # Check entities
        async with self.memory_system.graph.Session() as session:
            result = await session.execute(select(Entity.name))
            entities = result.scalars().all()
            self.assertNotIn("TestEntity", entities)
            self.assertIn("OtherEntity", entities)
            self.assertIn("ThirdEntity", entities)

            # Check relations involving TestEntity are gone
            result = await session.execute(select(Relation).where(Relation.source_id == 1)) # Assuming ID 1 for TestEntity
            relations = result.scalars().all()
            # We don't know IDs for sure, so better query by join or count
            # But let's just assume if entity is gone, cascade or manual delete worked.
            # GraphManager.delete_entity manually deletes relations first.

            # Verify total relations count. Originally 2 relations:
            # Test -> Other
            # Other -> Third
            # After deleting TestEntity, Test->Other should be gone. Other->Third remains.
            result = await session.execute(select(func.count(Relation.id)))
            rel_count = result.scalar()
            self.assertEqual(rel_count, 1, "Should have 1 relation remaining")

        # Total Count Check
        # Episodic: 2
        # Semantic: 1
        # Procedural: 1
        # Graph: 1 (entity)
        # Total: 5
        self.assertEqual(count, 5)

if __name__ == "__main__":
    unittest.main()
