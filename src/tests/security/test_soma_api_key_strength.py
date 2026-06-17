import pytest
from fastapi.testclient import TestClient
from src.ippoc.soma.server import app
import re

client = TestClient(app)

def test_api_key_strength():
    response = client.post("/v1/auth/issue", params={"node_id": "test-node"})
    assert response.status_code == 200
    data = response.json()
    assert "api_key" in data
    api_key = data["api_key"]

    # A UUID is 36 chars long, urlsafe token with 32 bytes is 43 chars long.
    # It shouldn't be a UUID
    uuid_pattern = re.compile(r'^[0-9a-f]{8}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{12}$', re.IGNORECASE)
    assert not uuid_pattern.match(api_key), "API key should not be a UUID"
    assert len(api_key) > 36, "API key length should be greater than 36 for higher entropy"
