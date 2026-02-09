
import os
import sys
import unittest
from unittest.mock import MagicMock, patch
from fastapi.testclient import TestClient

# Ensure src is in path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "../..")))

# Set dummy API key
os.environ["GOOGLE_API_KEY"] = "dummy"

# Mock dependencies to prevent side effects during import
mock_pgvector = MagicMock()
mock_langchain_community = MagicMock()
mock_langchain_community.vectorstores.PGVector = mock_pgvector

# We need to patch BEFORE importing mnemosyne.api.server
sys.modules["psycopg2"] = MagicMock()

# Patch PGVector in the place where it is imported FROM
with patch("langchain_community.vectorstores.PGVector", mock_pgvector):
    try:
        import mnemosyne.api.server
    except ImportError:
        pass

class TestAPISecurity(unittest.TestCase):
    def setUp(self):
        # We need to make sure the module is loaded
        if 'mnemosyne.api.server' not in sys.modules:
             pass

        # Check if app is loaded
        from mnemosyne.api.server import app
        self.client = TestClient(app)

        # Patch the API Key used by the server
        self.api_key = "test-secret-key"
        self.patcher_key = patch("mnemosyne.api.server.MNEMOSYNE_API_KEY", self.api_key)
        self.patcher_key.start()

    def tearDown(self):
        self.patcher_key.stop()

    def test_search_memory_no_auth(self):
        """Test that searching memory without auth returns 403 or 401."""
        response = self.client.post("/v1/memory/search", json={"query": "test"})
        # 403 if HTTPBearer handles it strictly, or 401 if missing header
        self.assertIn(response.status_code, [401, 403], f"Expected 401/403, got {response.status_code}")

    def test_search_memory_invalid_auth(self):
        """Test that searching memory with invalid auth returns 403."""
        headers = {"Authorization": "Bearer invalid-token"}
        response = self.client.post("/v1/memory/search", json={"query": "test"}, headers=headers)
        self.assertEqual(response.status_code, 403, f"Expected 403 Forbidden, got {response.status_code}")

    def test_search_memory_valid_auth(self):
        """Test that searching memory with valid auth succeeds (or at least passes auth)."""
        headers = {"Authorization": f"Bearer {self.api_key}"}

        # We expect 500 because the mock DB/LLM will fail, but NOT 401/403
        response = self.client.post("/v1/memory/search", json={"query": "test"}, headers=headers)
        self.assertNotEqual(response.status_code, 401)
        self.assertNotEqual(response.status_code, 403)
        # Ideally we'd fix the mock so it returns 200, but for security test, passing auth is enough.

    def test_consolidate_memory_no_auth(self):
        """Test that consolidating memory without auth returns 401/403."""
        response = self.client.post("/v1/memory/consolidate", json={"content": "test"})
        self.assertIn(response.status_code, [401, 403], f"Expected 401/403, got {response.status_code}")

    def test_consolidate_memory_valid_auth(self):
        """Test that consolidating memory with valid auth passes auth."""
        headers = {"Authorization": f"Bearer {self.api_key}"}

        # We expect failure later in the pipeline, but not auth failure
        response = self.client.post("/v1/memory/consolidate", json={"content": "test"}, headers=headers)
        self.assertNotEqual(response.status_code, 401)
        self.assertNotEqual(response.status_code, 403)

if __name__ == "__main__":
    unittest.main()
