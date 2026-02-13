import sys
import os
import unittest
from fastapi.testclient import TestClient

# Ensure src is in path so we can import ippoc
sys.path.append(os.path.join(os.getcwd(), "src"))

from ippoc.soma.server import app, api_keys

class TestSomaAuth(unittest.TestCase):
    def setUp(self):
        self.client = TestClient(app)
        self.test_key = "test-soma-key"
        self.node_id = "test-node"
        api_keys[self.test_key] = self.node_id

    def tearDown(self):
        if self.test_key in api_keys:
            del api_keys[self.test_key]

    def test_verify_auth_header(self):
        """Test that authentication via Authorization header works."""
        response = self.client.get("/v1/auth/verify", headers={"Authorization": f"Bearer {self.test_key}"})
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.json(), {"status": "valid", "node_id": self.node_id})

    def test_verify_auth_query_param_fails(self):
        """Test that authentication via query parameter fails (vulnerability fix)."""
        response = self.client.get(f"/v1/auth/verify?api_key={self.test_key}")
        # Expect 403 or 401 because header is missing
        self.assertIn(response.status_code, [401, 403])

    def test_verify_auth_missing_header(self):
        """Test that missing authorization header returns 403 or 401."""
        response = self.client.get("/v1/auth/verify")
        self.assertIn(response.status_code, [401, 403])

    def test_verify_auth_invalid_key(self):
        """Test that invalid key in header returns 401."""
        response = self.client.get("/v1/auth/verify", headers={"Authorization": "Bearer invalid-key"})
        self.assertEqual(response.status_code, 401)

if __name__ == "__main__":
    unittest.main()
