import pytest
import re
from fastapi.testclient import TestClient
from src.ippoc.soma.server import app, api_keys

client = TestClient(app)

def test_soma_api_key_strength():
    # Clear any existing keys
    api_keys.clear()

    # Issue a new key
    response = client.post("/v1/auth/issue?node_id=test-node")
    assert response.status_code == 200

    data = response.json()
    assert data["status"] == "success"
    assert "api_key" in data

    api_key = data["api_key"]

    # Verify the key is not a standard UUID (UUIDs are predictable/weak for API keys)
    # A standard UUID v4 looks like: xxxxxxxx-xxxx-4xxx-yxxx-xxxxxxxxxxxx
    uuid_pattern = re.compile(r'^[0-9a-f]{8}-[0-9a-f]{4}-4[0-9a-f]{3}-[89ab][0-9a-f]{3}-[0-9a-f]{12}$', re.IGNORECASE)
    assert not uuid_pattern.match(api_key), "API key appears to be a UUID, which is cryptographically weak"

    # Verify the key has sufficient entropy (length)
    # secrets.token_urlsafe(32) should generate a string of length ~43
    assert len(api_key) >= 32, f"API key is too short ({len(api_key)} chars), insufficient entropy"
