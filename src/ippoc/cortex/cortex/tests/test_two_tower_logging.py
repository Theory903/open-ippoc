import sys
import os
import pytest
import json
import asyncio
from unittest.mock import MagicMock, AsyncMock, patch

# Mock dependencies before import
sys.modules['langchain_core.messages'] = MagicMock()
sys.modules['langchain_google_genai'] = MagicMock()
sys.modules['langchain_ollama'] = MagicMock()

# Ensure src is in path
sys.path.append(os.path.join(os.getcwd(), 'src'))

from ippoc.cortex.cortex.two_tower import TwoTowerEngine
from ippoc.cortex.cortex.schemas import ActionCandidate

class TestTwoTowerEngine:

    @pytest.fixture
    def engine(self):
        engine = TwoTowerEngine()
        # Mock LLM B for validation
        engine.llm_b = MagicMock()
        engine.llm_b.ainvoke = AsyncMock(return_value=MagicMock(content="YES approved"))
        return engine

    @pytest.mark.asyncio
    async def test_log_pattern_async_execution(self, engine, tmp_path):
        # Use tmp_path for patterns file
        log_file = tmp_path / "patterns.jsonl"
        engine.patterns_file = str(log_file)

        candidate = ActionCandidate(
            action="test_action",
            confidence=0.9,
            expected_cost=0.1,
            risk="low",
            requires_validation=True,
            payload={"thought": "Test thought"}
        )

        # Should create the file and write to it
        await engine.validate_action(candidate)

        assert log_file.exists()
        content = log_file.read_text()
        data = json.loads(content)
        assert data["impulse"]["action"] == "test_action"
        assert data["validator_response"] == "YES APPROVED"
        assert data["approved"] is True

    @pytest.mark.asyncio
    async def test_log_pattern_uses_asyncio_to_thread(self, engine, tmp_path):
        log_file = tmp_path / "patterns.jsonl"
        engine.patterns_file = str(log_file)

        candidate = ActionCandidate(
            action="test_action",
            confidence=0.9,
            expected_cost=0.1,
            risk="low",
            requires_validation=True,
            payload={"thought": "Test thought"}
        )

        with patch("asyncio.to_thread", side_effect=asyncio.to_thread) as mock_to_thread:
            await engine.validate_action(candidate)

            # Verify asyncio.to_thread was called
            assert mock_to_thread.called
            # Verify it was called with _write_pattern_entry
            args, _ = mock_to_thread.call_args
            assert args[0] == engine._write_pattern_entry
