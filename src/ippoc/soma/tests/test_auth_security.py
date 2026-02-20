import unittest
from fastapi.testclient import TestClient
from ippoc.soma.server import app, api_keys

class TestAuthSecurity(unittest.TestCase):
    def setUp(self):
        self.client = TestClient(app)
        # Inject a test key
        self.test_key = "test-secret-key-123"
        self.node_id = "test-node"
        api_keys[self.test_key] = self.node_id

    def test_verify_api_key_query_param_rejected(self):
        """
        Verify that api_key in query params is REJECTED.
        """
        response = self.client.get(f"/v1/auth/verify?api_key={self.test_key}")
        # Should be 403 (Forbidden/Not Authenticated) or 401
        self.assertIn(response.status_code, [401, 403])

    def test_verify_api_key_header_accepted(self):
        """
        Verify that Bearer token in Authorization header is ACCEPTED.
        """
        headers = {"Authorization": f"Bearer {self.test_key}"}
        response = self.client.get("/v1/auth/verify", headers=headers)
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.json(), {"status": "valid", "node_id": self.node_id})

    def test_verify_invalid_api_key_header_rejected(self):
        """
        Verify that invalid Bearer token is REJECTED.
        """
        headers = {"Authorization": "Bearer invalid-key"}
        response = self.client.get("/v1/auth/verify", headers=headers)
        self.assertEqual(response.status_code, 401)

if __name__ == '__main__':
    unittest.main()
