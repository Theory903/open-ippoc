import pytest
import asyncio
from unittest.mock import MagicMock, patch, AsyncMock
import os

# Ensure mnemosyne can be imported
import sys
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '../../')))

from mnemosyne.hidb.client import HiDB, MemoryRecord

@pytest.mark.asyncio
async def test_hidb_initialization():
    hidb = HiDB(db_url="postgres://localhost:5432/test", redis_url="redis://localhost:6379/0")
    assert hidb.db_url == "postgres://localhost:5432/test"
    assert hidb.redis_url == "redis://localhost:6379/0"
    assert hidb.pool is None
    assert hidb.redis is None

@pytest.mark.asyncio
async def test_insert_memory():
    hidb = HiDB(db_url="postgres://test")

    # Mock pool and redis
    hidb.pool = AsyncMock()
    hidb.redis = AsyncMock()
    hidb._connected = True

    record = MemoryRecord(
        content="Test memory",
        embedding=[0.1] * 768
    )

    result_id = await hidb.insert_memory(record)

    assert result_id is not None
    # Check that execute was called
    hidb.pool.execute.assert_called_once()
    # Check that redis set was called
    hidb.redis.set.assert_called_once()

@pytest.mark.asyncio
async def test_semantic_search():
    hidb = HiDB(db_url="postgres://test")
    hidb.pool = AsyncMock()
    hidb._connected = True

    # Mock data
    mock_record = {
        'id': 'uuid-123',
        'embedding': [0.1] * 768,
        'content': 'Test result',
        'confidence': 1.0,
        'decay_rate': 0.1,
        'source': 'test',
        'created_at': '2023-01-01T00:00:00',
        'updated_at': '2023-01-01T00:00:00'
    }

    hidb.pool.fetch.return_value = [mock_record]

    results = await hidb.semantic_search([0.1] * 768)

    assert len(results) == 1
    assert results[0].id == 'uuid-123'
    assert results[0].content == 'Test result'

def test_global_instantiation():
    # Import locally to verify it works as expected when importing mnemosyne
    from mnemosyne import hidb
    assert isinstance(hidb, HiDB)
