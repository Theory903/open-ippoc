import unittest
import sys
import os
from fastapi.testclient import TestClient

# Ensure src/ippoc is in path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "../../../")))

from ippoc.soma.server import app, api_keys

client = TestClient(app)

class TestAuthSecurity(unittest.TestCase):
    def setUp(self):
        self.api_key = "secure-test-key"
        self.node_id = "test-node-secure"
        api_keys[self.api_key] = self.node_id

    def test_verify_header_success(self):
        """Test that verification succeeds with correct Bearer header."""
        response = client.get(
            "/v1/auth/verify",
            headers={"Authorization": f"Bearer {self.api_key}"}
        )
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.json(), {"status": "valid", "node_id": self.node_id})

    def test_verify_query_param_rejected(self):
        """Test that verification fails with query parameter (the vulnerability fix)."""
        response = client.get(f"/v1/auth/verify?api_key={self.api_key}")
        # Expect 403 Forbidden (Not Authenticated) or 401
        self.assertIn(response.status_code, [401, 403])

    def test_verify_no_auth_fails(self):
        """Test that verification fails with no authentication."""
        response = client.get("/v1/auth/verify")
        self.assertIn(response.status_code, [401, 403])

    def test_verify_invalid_key_fails(self):
        """Test that verification fails with invalid key in header."""
        response = client.get(
            "/v1/auth/verify",
            headers={"Authorization": "Bearer invalid-key"}
        )
        self.assertEqual(response.status_code, 401)
        self.assertEqual(response.json(), {"detail": "Invalid API key"})

if __name__ == "__main__":
    unittest.main()
