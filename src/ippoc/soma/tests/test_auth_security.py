import pytest
from fastapi.testclient import TestClient
from ippoc.soma.server import app, api_keys

client = TestClient(app)

# Helper to register an API key
def get_api_key():
    response = client.post("/v1/auth/issue")
    assert response.status_code == 200
    return response.json()["api_key"]

def test_verify_api_key_header():
    """Verify that the API key is accepted via Authorization header."""
    api_key = get_api_key()

    # Send Authorization: Bearer <token>
    headers = {"Authorization": f"Bearer {api_key}"}
    response = client.get("/v1/auth/verify", headers=headers)

    assert response.status_code == 200
    assert response.json()["status"] == "valid"

def test_verify_api_key_query_param_rejected():
    """Verify that the API key is NOT accepted via query parameter."""
    api_key = get_api_key()

    # Send API key as query param
    response = client.get("/v1/auth/verify", params={"api_key": api_key})

    # Expect 422 Unprocessable Entity because the header is missing
    # or 401 Unauthorized if the server implementation handles it explicitly
    assert response.status_code in [401, 422]
