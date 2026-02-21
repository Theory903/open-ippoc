import pytest
from fastapi.testclient import TestClient
from ippoc.soma.server import app, api_keys

client = TestClient(app)

def test_api_key_generation_security():
    """
    Verify that API keys are generated using a cryptographically secure method (secrets)
    instead of predictable UUIDs.
    UUID4 is 36 chars. secrets.token_urlsafe(32) is ~43 chars.
    """
    response = client.post("/v1/auth/issue")
    assert response.status_code == 200
    data = response.json()
    api_key = data["api_key"]

    # Check length to distinguish from standard UUID (36 chars)
    # token_urlsafe(32) -> 43 chars usually
    assert len(api_key) > 36, f"API Key should be longer than a UUID (36), got {len(api_key)}"

def test_api_key_verification_rejects_query_param():
    """
    Verify that passing api_key in query params is rejected.
    This prevents sensitive data leakage in access logs.
    """
    # Issue a key first
    response = client.post("/v1/auth/issue")
    api_key = response.json()["api_key"]

    # Try to verify using query param (Old insecure way)
    response = client.get(f"/v1/auth/verify?api_key={api_key}")

    # Should fail with 401/403 (missing bearer) or 422 (validation error)
    # HTTPBearer usually returns 403 Not Authenticated if auto_error=True (default)
    assert response.status_code in [401, 403, 422], f"Should reject query param, got {response.status_code}"

def test_api_key_verification_accepts_bearer_header():
    """
    Verify that passing api_key in Authorization header works.
    """
    # Issue a key first
    response = client.post("/v1/auth/issue")
    api_key = response.json()["api_key"]

    # Verify using Bearer header
    headers = {"Authorization": f"Bearer {api_key}"}
    response = client.get("/v1/auth/verify", headers=headers)

    assert response.status_code == 200
    assert response.json()["status"] == "valid"

def test_api_key_verification_rejects_invalid_bearer():
    """
    Verify that invalid Bearer token is rejected.
    """
    headers = {"Authorization": "Bearer invalid-token-123"}
    response = client.get("/v1/auth/verify", headers=headers)

    assert response.status_code in [401, 403]
