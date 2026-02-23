import pytest
from fastapi.testclient import TestClient
from ippoc.soma.server import app

client = TestClient(app)

def test_api_key_generation_security():
    """
    Verify that generated API keys are cryptographically strong.
    """
    response = client.post("/v1/auth/issue", json={"node_id": "test-node"})
    assert response.status_code == 200
    data = response.json()
    api_key = data["api_key"]

    # Check length. UUID is 36. Secure token (32 bytes urlsafe) is usually 43.
    # We assert strict security requirements which should fail on UUID.
    assert len(api_key) > 40, f"API Key too short: {len(api_key)} chars (likely UUID)"

    # Check entropy/format. UUID usually has hyphens. URL-safe base64 usually doesn't
    # (except maybe '-' and '_', but not in 8-4-4-4-12 format).
    # We rely on length check to distinguish from UUID (36 chars).
    pass
