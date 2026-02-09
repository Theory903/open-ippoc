import pytest
from fastapi.testclient import TestClient
from unittest.mock import MagicMock, AsyncMock, patch
import os
import sys

# Mock Environment variables
os.environ["GOOGLE_API_KEY"] = "dummy"

# We need to mock the singleton 'hidb' instance exported by 'mnemosyne' package
# AND the HiDB class used in other places if any.

# Mocking external dependencies
with patch("mnemosyne.hidb.client.HiDB"), \
     patch("langchain_google_genai.ChatGoogleGenerativeAI"), \
     patch("langchain_google_genai.GoogleGenerativeAIEmbeddings"), \
     patch("langchain_community.vectorstores.PGVector"):

    from mnemosyne.api.server import app
    from mnemosyne import hidb as global_hidb

client = TestClient(app)

@pytest.mark.asyncio
async def test_store_memory_hidb():
    # Mock insert_memory on the global instance
    global_hidb.insert_memory = AsyncMock(return_value="uuid-123")

    payload = {
        "content": "Test memory content",
        "vector": [0.1] * 768,
        "metadata": {"source": "test"}
    }

    response = client.post("/v1/memory/store", json=payload)

    assert response.status_code == 200
    assert response.json() == {"id": "uuid-123", "status": "stored"}
    global_hidb.insert_memory.assert_called_once()

@pytest.mark.asyncio
async def test_search_memory_hidb():
    # Mock semantic_search
    mock_record = MagicMock()
    mock_record.id = "uuid-123"
    mock_record.content = "Test result"
    mock_record.metadata = {}
    mock_record.confidence = 0.9
    mock_record.score = 0.85  # Similarity score

    global_hidb.semantic_search = AsyncMock(return_value=[mock_record])

    payload = {
        "vector": [0.1] * 768,
        "limit": 3
    }

    response = client.post("/v1/memory/search", json=payload)

    assert response.status_code == 200
    results = response.json()
    assert len(results) == 1
    assert results[0]["id"] == "uuid-123"
    assert results[0]["content"] == "Test result"
    assert results[0]["score"] == 0.85
    global_hidb.semantic_search.assert_called_once()

@pytest.mark.asyncio
async def test_search_memory_missing_params():
    payload = {"limit": 5}
    # This should fail validation or raise 400
    response = client.post("/v1/memory/search", json=payload)
    assert response.status_code == 400
    assert "required" in response.json()["detail"]
