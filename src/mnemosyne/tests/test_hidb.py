import unittest
from unittest.mock import MagicMock, AsyncMock, patch
import os
import sys

# Ensure src is in path
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "../..")))

from mnemosyne.hidb import HiDB

class TestHiDB(unittest.IsolatedAsyncioTestCase):

    async def asyncSetUp(self):
        # Patch create_async_engine and redis
        self.patcher_engine = patch("mnemosyne.hidb.client.create_async_engine")
        self.mock_create_engine = self.patcher_engine.start()
        self.mock_engine = MagicMock()
        self.mock_create_engine.return_value = self.mock_engine

        self.patcher_redis = patch("mnemosyne.hidb.client.redis.from_url")
        self.mock_redis_from_url = self.patcher_redis.start()
        self.mock_redis = AsyncMock()
        self.mock_redis_from_url.return_value = self.mock_redis

    async def asyncTearDown(self):
        self.patcher_engine.stop()
        self.patcher_redis.stop()

    async def test_instantiation(self):
        hidb = HiDB(db_url="sqlite+aiosqlite:///:memory:", redis_url="redis://mock")
        self.assertIsNotNone(hidb.engine)
        self.assertIsNotNone(hidb.redis)
        self.mock_create_engine.assert_called_with("sqlite+aiosqlite:///:memory:", echo=False)
        self.mock_redis_from_url.assert_called_with("redis://mock", decode_responses=True)

    async def test_insert_memory(self):
        hidb = HiDB()

        # Mock Session
        mock_session_inst = AsyncMock()
        hidb._async_session = MagicMock(return_value=mock_session_inst)

        # Setup session add/commit
        mock_session = mock_session_inst.__aenter__.return_value
        mock_session.add = MagicMock()

        # Act
        mem_id = await hidb.insert_memory("Test Content", [0.1]*768, source="test")

        # Assert
        self.assertIsInstance(mem_id, str)
        mock_session.add.assert_called_once()
        mock_session.commit.assert_called_once()

        # Verify content of added object
        added_obj = mock_session.add.call_args[0][0]
        self.assertEqual(added_obj.content, "Test Content")
        self.assertEqual(added_obj.source, "test")

    async def test_semantic_search(self):
        hidb = HiDB()

        # Mock Session
        mock_session_inst = AsyncMock()
        hidb._async_session = MagicMock(return_value=mock_session_inst)
        mock_session = mock_session_inst.__aenter__.return_value

        # Mock result
        mock_result = MagicMock()
        mock_obj = MagicMock()
        mock_obj.id = "uuid-123"
        mock_obj.content = "Result Content"
        mock_obj.source = "test"
        mock_obj.confidence = 1.0
        mock_obj.created_at = None

        mock_result.scalars.return_value.all.return_value = [mock_obj]
        mock_session.execute.return_value = mock_result

        # Act
        results = await hidb.semantic_search([0.1]*768)

        # Assert
        self.assertEqual(len(results), 1)
        self.assertEqual(results[0]["id"], "uuid-123")
        self.assertEqual(results[0]["content"], "Result Content")

if __name__ == "__main__":
    unittest.main()
