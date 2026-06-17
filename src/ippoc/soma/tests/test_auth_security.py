
from fastapi.testclient import TestClient
import sys
import os

# Add src to path to import correctly
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "../../../..")))

from src.ippoc.soma.server import app, api_keys

client = TestClient(app)

def test_verify_auth_rejects_query_param():
    """
    Test that the verify endpoint rejects API keys passed as query parameters.
    This prevents secret leakage in logs.
    """
    # Setup
    api_key = "test-key-vuln"
    api_keys[api_key] = "test-node"

    # Test query param (Vulnerable way)
    response = client.get(f"/v1/auth/verify?api_key={api_key}")

    # Assert failure (403/401/422 expected when fix is applied)
    # If vulnerable, this returns 200.
    assert response.status_code in [401, 403, 422], f"Vulnerability exposed! API accepted query param with status {response.status_code}"

def test_verify_auth_accepts_bearer_token():
    """
    Test that the verify endpoint accepts API keys passed as Bearer tokens.
    """
    # Setup
    api_key = "test-key-secure"
    api_keys[api_key] = "test-node"

    # Test Bearer token (Secure way)
    headers = {"Authorization": f"Bearer {api_key}"}
    response = client.get("/v1/auth/verify", headers=headers)

    # Assert success
    assert response.status_code == 200
    assert response.json()["status"] == "valid"
    assert response.json()["node_id"] == "test-node"

def test_verify_auth_rejects_invalid_bearer_token():
    """
    Test that invalid tokens are rejected.
    """
    # Test Invalid Bearer token
    headers = {"Authorization": "Bearer invalid-key-999"}
    response = client.get("/v1/auth/verify", headers=headers)

    # Assert unauthorized
    assert response.status_code == 401
