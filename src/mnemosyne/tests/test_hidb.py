import pytest
import uuid
from unittest.mock import MagicMock, AsyncMock, patch, PropertyMock
from mnemosyne.hidb.hidb import HiDB
from mnemosyne.hidb.models import Memory, CausalLink

@pytest.fixture
def mock_engine():
    with patch("mnemosyne.hidb.hidb.create_async_engine") as mock:
        engine = MagicMock()
        mock.return_value = engine
        yield mock

@pytest.mark.asyncio
async def test_init_db(mock_engine):
    hidb = HiDB(db_url="postgresql+asyncpg://user:pass@localhost:5432/test_db")

    engine_instance = mock_engine.return_value

    # Mock engine.begin() to return an async context manager
    cm = MagicMock()
    conn = AsyncMock()
    cm.__aenter__ = AsyncMock(return_value=conn)
    cm.__aexit__ = AsyncMock(return_value=None)

    engine_instance.begin.return_value = cm

    await hidb.init_db()

    engine_instance.begin.assert_called_once()
    cm.__aenter__.assert_awaited_once()
    conn.run_sync.assert_called_once()

@pytest.mark.asyncio
async def test_store_memory(mock_engine):
    hidb = HiDB()

    session = AsyncMock()
    session.add = MagicMock() # session.add is synchronous

    # Mock the property async_session on the class
    with patch('mnemosyne.hidb.hidb.HiDB.async_session', new_callable=PropertyMock) as mock_prop:
        mock_session_maker = MagicMock()
        mock_prop.return_value = mock_session_maker
        mock_session_maker.return_value.__aenter__.return_value = session

        memory_id = await hidb.store_memory(
            content="Test memory",
            embedding=[0.1] * 768,
            source="test"
        )

        session.add.assert_called_once()
        session.commit.assert_awaited_once()
        session.refresh.assert_awaited_once()

        args, _ = session.add.call_args
        assert isinstance(args[0], Memory)
        assert args[0].content == "Test memory"

@pytest.mark.asyncio
async def test_search_memories(mock_engine):
    hidb = HiDB()

    session = AsyncMock()
    session.add = MagicMock()

    with patch('mnemosyne.hidb.hidb.HiDB.async_session', new_callable=PropertyMock) as mock_prop:
        mock_session_maker = MagicMock()
        mock_prop.return_value = mock_session_maker
        mock_session_maker.return_value.__aenter__.return_value = session

        # result of session.execute is a Result object (sync methods)
        mock_result = MagicMock()
        mock_result.scalars.return_value.all.return_value = [
            Memory(content="Result 1", confidence=0.9),
            Memory(content="Result 2", confidence=0.8)
        ]
        session.execute.return_value = mock_result

        results = await hidb.search_memories(
            query_embedding=[0.1] * 768,
            limit=5
        )

        assert len(results) == 2
        session.execute.assert_awaited_once()

@pytest.mark.asyncio
async def test_link_memories(mock_engine):
    hidb = HiDB()

    session = AsyncMock()
    session.add = MagicMock() # session.add is synchronous

    with patch('mnemosyne.hidb.hidb.HiDB.async_session', new_callable=PropertyMock) as mock_prop:
        mock_session_maker = MagicMock()
        mock_prop.return_value = mock_session_maker
        mock_session_maker.return_value.__aenter__.return_value = session

        source = uuid.uuid4()
        target = uuid.uuid4()

        link_id = await hidb.link_memories(source, target)

        session.add.assert_called_once()
        session.commit.assert_awaited_once()

        args, _ = session.add.call_args
        assert isinstance(args[0], CausalLink)
        assert args[0].from_memory_id == source
        assert args[0].to_memory_id == target

@pytest.mark.asyncio
async def test_get_context(mock_engine):
    hidb = HiDB()

    session = AsyncMock()
    session.add = MagicMock()

    with patch('mnemosyne.hidb.hidb.HiDB.async_session', new_callable=PropertyMock) as mock_prop:
        mock_session_maker = MagicMock()
        mock_prop.return_value = mock_session_maker
        mock_session_maker.return_value.__aenter__.return_value = session

        # Mock results
        mock_result_out = MagicMock()
        mock_result_out.scalars.return_value.all.return_value = [CausalLink(id=uuid.uuid4())]

        mock_result_in = MagicMock()
        mock_result_in.scalars.return_value.all.return_value = [CausalLink(id=uuid.uuid4())]

        # side_effect for execute to return different results
        session.execute.side_effect = [mock_result_out, mock_result_in]

        context = await hidb.get_context(uuid.uuid4())

        assert len(context["outgoing"]) == 1
        assert len(context["incoming"]) == 1
        assert session.execute.call_count == 2
