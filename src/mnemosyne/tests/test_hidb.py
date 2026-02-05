import unittest
from unittest.mock import MagicMock, patch
import os
import sys

# Add src to path
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '../../')))

from mnemosyne.hidb.client import HiDB, Record

class TestHiDB(unittest.TestCase):

    @patch('mnemosyne.hidb.client.redis')
    @patch('mnemosyne.hidb.client.PGVector')
    @patch('mnemosyne.hidb.client.GoogleGenerativeAIEmbeddings')
    def test_init_with_defaults(self, mock_embeddings, mock_pgvector, mock_redis):
        # Setup mocks
        mock_redis.from_url.return_value = MagicMock()
        mock_embeddings.return_value = MagicMock()

        # Act
        # Mock os.getenv to simulate API key presence for embeddings
        with patch.dict(os.environ, {"GOOGLE_API_KEY": "fake_key"}):
            hidb = HiDB()

        # Assert
        self.assertIsNotNone(hidb)

    @patch('mnemosyne.hidb.client.redis')
    @patch('mnemosyne.hidb.client.PGVector')
    def test_insert_memory(self, mock_pgvector, mock_redis):
        # Setup
        mock_vector_store = MagicMock()
        mock_pgvector.return_value = mock_vector_store
        mock_vector_store.add_documents.return_value = ["test-id"]

        mock_redis_client = MagicMock()
        mock_redis.from_url.return_value = mock_redis_client

        # Embeddings mock
        embeddings = MagicMock()

        hidb = HiDB(embeddings=embeddings)

        record = {
            "content": "test content",
            "metadata": {"source": "test"}
        }

        # Act
        result_id = hidb.insert_memory(record)

        # Assert
        self.assertEqual(result_id, "test-id")
        mock_vector_store.add_documents.assert_called_once()
        mock_redis_client.set.assert_called_once()

    @patch('mnemosyne.hidb.client.PGVector')
    def test_semantic_search(self, mock_pgvector):
        # Setup
        mock_vector_store = MagicMock()
        mock_pgvector.return_value = mock_vector_store

        # Mock result from vector store
        mock_doc = MagicMock()
        mock_doc.page_content = "result content"
        mock_doc.metadata = {"id": "res-1"}
        mock_vector_store.similarity_search_by_vector_with_score.return_value = [(mock_doc, 0.9)]

        embeddings = MagicMock()
        hidb = HiDB(embeddings=embeddings)

        vector = [0.1, 0.2, 0.3]

        # Act
        results = hidb.semantic_search(vector)

        # Assert
        self.assertEqual(len(results), 1)
        self.assertEqual(results[0].content, "result content")
        self.assertEqual(results[0].score, 0.9)
        mock_vector_store.similarity_search_by_vector_with_score.assert_called_with(vector, k=5)

if __name__ == '__main__':
    unittest.main()
