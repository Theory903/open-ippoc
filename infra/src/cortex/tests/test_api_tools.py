# brain/tests/test_api_tools.py

from fastapi.testclient import TestClient
from cortex.cortex.server import app
from cortex.core.bootstrap import bootstrap_tools

# Auth Header
HEADERS = {"Authorization": "Bearer ippoc-secret-key"}

def run_tests():
    # Use context manager to trigger lifespan (startup/shutdown)
    with TestClient(app) as client:
        # 1. Health Check
        response = client.get("/health")
        assert response.status_code == 200
        data = response.json()
        assert data["auth_enabled"] is True
        print("✅ Health Check Passed")

        # 2. Authorized Tool Execution
        payload = {
            "tool_name": "research",
            "domain": "cognition",
            "action": "digest_paper",
            "context": {"url": "http://test.com/paper.pdf"},
            "risk_level": "low",
            "estimated_cost": 2.0
        }
        resp_auth = client.post("/v1/tools/execute", json=payload, headers=HEADERS)
        if resp_auth.status_code != 200:
            print(f"Auth Failed: {resp_auth.status_code} {resp_auth.text}")
        assert resp_auth.status_code == 200
        assert resp_auth.json()["success"] is True
        print("✅ Authorized Request Passed")

        # 3. Unauthorized (Missing Header)
        resp_unauth = client.post("/v1/tools/execute", json=payload)
        assert resp_unauth.status_code == 403
        assert resp_unauth.json()["detail"] == "Not authenticated"
        print("✅ Unauthorized (Missing) Blocked")

        # 4. Unauthorized (Wrong Header)
        resp_wrong = client.post("/v1/tools/execute", json=payload, headers={"Authorization": "Bearer wrong-key"})
        assert resp_wrong.status_code == 403
        assert resp_wrong.json()["detail"] == "Invalid API Key"
        print("✅ Unauthorized (Wrong) Blocked")

if __name__ == "__main__":
    try:
        run_tests()
    except Exception as e:
        print(f"❌ API Auth Test Failed: {e}")
