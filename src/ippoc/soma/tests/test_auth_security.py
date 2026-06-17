from fastapi.testclient import TestClient
from src.ippoc.soma.server import app
import uuid

client = TestClient(app)

def test_issue_api_key_returns_secure_token():
    response = client.post("/v1/auth/issue")
    assert response.status_code == 200
    data = response.json()
    assert data["status"] == "success"
    api_key = data["api_key"]

    # Verify it is NOT a valid UUID (since we switched to secrets.token_urlsafe)
    try:
        uuid.UUID(api_key, version=4)
        is_uuid = True
    except ValueError:
        is_uuid = False

    assert not is_uuid, "API key should not be a UUID, but a secure random token"
    assert len(api_key) > 32, "API key should be sufficiently long"
