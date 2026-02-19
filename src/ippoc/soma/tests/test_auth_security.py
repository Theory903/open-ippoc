import sys
import os
import unittest
from fastapi.testclient import TestClient

# Add src to pythonpath
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "../../../../")))

try:
    from src.ippoc.soma.server import app
except ImportError:
    # If run from repo root
    from src.ippoc.soma.server import app

client = TestClient(app)

class TestAuthSecurity(unittest.TestCase):
    def test_auth_flow_secure(self):
        # 1. Issue a key
        response = client.post("/v1/auth/issue")
        self.assertEqual(response.status_code, 200)
        data = response.json()
        self.assertIn("api_key", data)
        api_key = data["api_key"]

        # 2. Verify with Header (The Secure Way)
        # This MUST succeed (200 OK)
        response = client.get(
            "/v1/auth/verify",
            headers={"Authorization": f"Bearer {api_key}"}
        )
        self.assertEqual(response.status_code, 200, "Header verification failed")
        self.assertEqual(response.json()["status"], "valid")

        # 3. Verify with Query Param (The Insecure Way)
        # This MUST fail (403 Forbidden or 422 Unprocessable Entity depending on FastAPI handling of missing dependency)
        # Since HTTPBearer is a dependency, if the header is missing, it returns 403 Forbidden (Not Authenticated)
        response = client.get(f"/v1/auth/verify?api_key={api_key}")
        self.assertNotEqual(response.status_code, 200, "Query param verification should fail")
        self.assertIn(response.status_code, [403, 401, 422], f"Unexpected status code: {response.status_code}")

if __name__ == "__main__":
    unittest.main()
