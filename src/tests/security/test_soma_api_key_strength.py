import pytest
import re
from fastapi.testclient import TestClient

from src.ippoc.soma.server import app

client = TestClient(app)

def test_api_key_is_cryptographically_secure():
    """
    Test that the generated API key is cryptographically secure
    and not just a standard UUID.
    """
    response = client.post("/v1/auth/issue")
    assert response.status_code == 200

    data = response.json()
    assert "api_key" in data
    api_key = data["api_key"]

    # Check length (secrets.token_urlsafe(32) should generate a 43 character string)
    assert len(api_key) >= 43

    # Ensure it does NOT look like a standard UUID
    # UUID pattern: 8-4-4-4-12 hex digits
    uuid_pattern = re.compile(r'^[0-9a-f]{8}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{12}$', re.IGNORECASE)
    assert not uuid_pattern.match(api_key), "API key should not be a standard UUID due to low entropy for secrets"

def test_api_key_verification():
    """
    Verify the entire API key generation and validation flow works as expected
    with the new cryptographically secure keys.
    """
    # 1. Issue a new API key
    issue_response = client.post("/v1/auth/issue?node_id=test-node")
    assert issue_response.status_code == 200
    api_key = issue_response.json()["api_key"]

    # 2. Verify the generated API key
    verify_response = client.get(f"/v1/auth/verify?api_key={api_key}")
    assert verify_response.status_code == 200
    assert verify_response.json()["status"] == "valid"
    assert verify_response.json()["node_id"] == "test-node"
