import pytest
import asyncio
import json
import sys
from unittest.mock import MagicMock, AsyncMock, patch

# Mock dependencies before imports
sys.modules["cortex.cortex.two_tower"] = MagicMock()
sys.modules["cortex.cortex.langgraph_engine"] = MagicMock()
sys.modules["cortex.cortex.telepathy"] = MagicMock()
sys.modules["cortex.cortex.persistence"] = MagicMock()
sys.modules["prometheus_client"] = MagicMock()
sys.modules["opentelemetry"] = MagicMock()
sys.modules["cortex.gateway.openclaw_adapter"] = MagicMock()
sys.modules["cortex.gateway.proprioception_scanner"] = MagicMock()

# Ensure we can import bootstrap
# But bootstrap imports openclaw_adapter etc.
# With sys.modules mocked, it should be fine.

from cortex.cortex.schemas import UserIntent
from cortex.core.intents import Intent, IntentType
from cortex.core.redis_queue import RedisQueue
# We import AutonomyController later to allow patching get_planner_queue

# Mock Redis client
@pytest.fixture
def mock_redis_client():
    mock_client = AsyncMock()
    mock_client.xadd = AsyncMock()
    mock_client.xreadgroup = AsyncMock(return_value=[])
    mock_client.xack = AsyncMock()
    mock_client.xgroup_create = AsyncMock()
    return mock_client

@pytest.fixture
def planner_queue(mock_redis_client):
    with patch("cortex.core.redis_queue.redis.from_url", return_value=mock_redis_client):
        queue = RedisQueue("redis://mock", "stream", "group", "consumer")
        return queue

@pytest.mark.asyncio
async def test_submit_intent_endpoint(planner_queue):
    # Import submit_intent inside test to patch planner_queue
    # We might need to mock other things that server.py imports

    # Pre-import cortex.core.bootstrap to avoid AttributeError during patch?
    # Or just mock it in sys.modules if we don't need its logic
    # server.py imports bootstrap_tools from cortex.core.bootstrap

    # Let's mock cortex.core.bootstrap completely
    mock_bootstrap = MagicMock()
    sys.modules["cortex.core.bootstrap"] = mock_bootstrap

    from cortex.cortex.server import submit_intent

    # We patch the planner_queue GLOBAL variable in server.py
    with patch("cortex.cortex.server.planner_queue", planner_queue):
        user_intent = UserIntent(
            description="Fix bugs",
            priority=0.8,
            intent_type="maintain",
            source="user_test",
            context={"foo": "bar"}
        )

        result = await submit_intent(user_intent)

        assert result["status"] == "queued"
        assert "intent_id" in result

        # Verify enqueue called
        planner_queue.client.xadd.assert_called_once()
        args, kwargs = planner_queue.client.xadd.call_args
        assert args[0] == planner_queue.stream
        assert "envelope" in args[1]
        envelope = json.loads(args[1]["envelope"])
        assert envelope["description"] == "Fix bugs"

@pytest.mark.asyncio
async def test_autonomy_controller_consumes_intent(planner_queue, mock_redis_client):
    # Setup mock data for fetch
    msg_id = b"123-0"
    intent_data = {
        "description": "Explore the world",
        "priority": 0.5,
        "intent_type": "explore",
        "source": "api",
        "context": {}
    }
    payload = {
        b"execution_id": b"abc-123",
        b"envelope": json.dumps(intent_data).encode()
    }

    # xreadgroup returns list of [stream_name, messages]
    # messages is list of [msg_id, fields]
    mock_redis_client.xreadgroup.return_value = [
        [b"stream", [(msg_id, payload)]]
    ]

    # Patch dependencies to avoid side effects during import or init
    with patch("cortex.core.autonomy.get_ledger"), \
         patch("cortex.core.autonomy.get_orchestrator"), \
         patch("cortex.core.autonomy.get_economy"), \
         patch("cortex.core.autonomy.collect_signals", new_callable=AsyncMock), \
         patch("cortex.core.autonomy.get_trust_model"), \
         patch("cortex.core.autonomy.get_hippocampus"), \
         patch("cortex.core.autonomy.get_evolver"), \
         patch("cortex.core.autonomy.get_planner_queue", return_value=planner_queue), \
         patch("os.path.exists", return_value=False): # prevent loading state

        from cortex.core.autonomy import AutonomyController

        controller = AutonomyController()
        # Manually ensure intent stack is empty
        controller.intent_stack.intents = []

        # Call process external requests
        await controller._process_external_requests()

        # Verify intent added
        assert len(controller.intent_stack.intents) == 1
        added_intent = controller.intent_stack.intents[0]
        assert added_intent.description == "Explore the world"
        assert added_intent.intent_type == IntentType.EXPLORE

        # Verify ack called
        mock_redis_client.xack.assert_called_once_with(planner_queue.stream, planner_queue.group, "123-0")
