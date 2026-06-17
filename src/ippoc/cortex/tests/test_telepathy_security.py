import unittest
from unittest.mock import patch, mock_open, MagicMock, ANY
import asyncio
import os
import sys

# Ensure src is in python path
sys.path.append(os.path.join(os.getcwd(), "src"))

from ippoc.cortex.cortex.telepathy import TelepathySwarm, MAX_MSG_SIZE
from ippoc.cortex.cortex.schemas import TelepathyMessage

class TestTelepathySecurity(unittest.TestCase):
    def setUp(self):
        self.swarm = TelepathySwarm(node_id="test-node", transports=[])

    @patch("builtins.open", new_callable=mock_open)
    def test_valid_message(self, mock_file):
        """Test that a valid message is processed correctly."""
        msg = TelepathyMessage(type="THOUGHT", sender="safe_sender", content="hello world")
        asyncio.run(self.swarm.handle_incoming(msg))

        # Check if file was opened
        mock_file.assert_called_with("ippoc_event_bus.log", "a")
        # Check if write was called
        handle = mock_file()
        handle.write.assert_called()

    @patch("builtins.open", new_callable=mock_open)
    def test_invalid_sender(self, mock_file):
        """Test that a message with an invalid sender is rejected."""
        msg = TelepathyMessage(type="THOUGHT", sender="bad/sender", content="hello")
        asyncio.run(self.swarm.handle_incoming(msg))

        # Should NOT write to file
        mock_file.assert_not_called()

    @patch("builtins.open", new_callable=mock_open)
    def test_large_message(self, mock_file):
        """Test that a large message is truncated."""
        content = "a" * (65 * 1024 + 1) # > 64KB
        msg = TelepathyMessage(type="THOUGHT", sender="safe_sender", content=content)
        asyncio.run(self.swarm.handle_incoming(msg))

        # It should still write, but truncated content
        mock_file.assert_called_with("ippoc_event_bus.log", "a")
        handle = mock_file()
        # Get arguments of write call
        args, _ = handle.write.call_args
        written_data = args[0]

        # Check if truncated marker is present
        self.assertIn("...(truncated)", written_data)
        # Check length is reasonable (json overhead + MAX_MSG_SIZE + truncated msg)
        self.assertTrue(len(written_data) < len(content))

    @patch("os.path.exists")
    @patch("os.path.getsize")
    @patch("os.rename")
    @patch("builtins.open", new_callable=mock_open)
    def test_log_rotation(self, mock_file, mock_rename, mock_getsize, mock_exists):
        """Test log rotation."""
        mock_exists.return_value = True
        mock_getsize.return_value = 11 * 1024 * 1024 # 11MB
        msg = TelepathyMessage(type="THOUGHT", sender="safe_sender", content="hello")

        asyncio.run(self.swarm.handle_incoming(msg))

        mock_rename.assert_called_with("ippoc_event_bus.log", "ippoc_event_bus.log.old")
        # And it should still write the new message
        mock_file.assert_called_with("ippoc_event_bus.log", "a")

if __name__ == "__main__":
    unittest.main()
