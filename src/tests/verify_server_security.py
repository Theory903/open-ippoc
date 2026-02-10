import sys
import os
import unittest
from unittest.mock import MagicMock, patch

# Mock dependencies
sys.modules["uvicorn"] = MagicMock()
sys.modules["fastapi"] = MagicMock()
sys.modules["fastapi.security"] = MagicMock()
sys.modules["fastapi.responses"] = MagicMock()
sys.modules["nest_asyncio"] = MagicMock()
sys.modules["contextlib"] = MagicMock()
sys.modules["prometheus_client"] = MagicMock()
sys.modules["opentelemetry"] = MagicMock()
sys.modules["opentelemetry.sdk.resources"] = MagicMock()
sys.modules["opentelemetry.sdk.trace"] = MagicMock()
sys.modules["opentelemetry.sdk.trace.export"] = MagicMock()
sys.modules["opentelemetry.exporter.otlp.proto.http.trace_exporter"] = MagicMock()

# Mock internal modules
sys.modules["cortex"] = MagicMock()
sys.modules["cortex.cortex"] = MagicMock()
sys.modules["cortex.cortex.schemas"] = MagicMock()
sys.modules["cortex.cortex.two_tower"] = MagicMock()
sys.modules["cortex.cortex.telepathy"] = MagicMock()
sys.modules["cortex.cortex.langgraph_engine"] = MagicMock()
sys.modules["cortex.core"] = MagicMock()
sys.modules["cortex.core.bootstrap"] = MagicMock()
sys.modules["cortex.core.orchestrator"] = MagicMock()
sys.modules["cortex.core.tools"] = MagicMock()
sys.modules["cortex.core.tools.base"] = MagicMock()
sys.modules["cortex.core.exceptions"] = MagicMock()
sys.modules["cortex.core.ledger"] = MagicMock()
sys.modules["cortex.core.redis_queue"] = MagicMock()
sys.modules["cortex.core.autonomy"] = MagicMock()
sys.modules["cortex.cortex.persistence"] = MagicMock()

# Path to server.py
SERVER_PATH = os.path.join(os.path.dirname(__file__), "..", "ippoc", "cortex", "cortex", "server.py")

class TestServerSecurity(unittest.TestCase):
    def setUp(self):
        # Reset environment
        if "IPPOC_PRODUCTION" in os.environ: del os.environ["IPPOC_PRODUCTION"]
        if "IPPOC_API_KEY" in os.environ: del os.environ["IPPOC_API_KEY"]
        if "IPPOC_AUTH_ENABLED" in os.environ: del os.environ["IPPOC_AUTH_ENABLED"]
        if "NODE_ID" in os.environ: del os.environ["NODE_ID"]

    def run_server_code(self):
        with open(SERVER_PATH, "r") as f:
            code = f.read()
        # Execute in a restricted scope but with mocked modules available
        exec(code, {"__name__": "__not_main__"})

    def test_production_missing_key_exits(self):
        """Test that server exits if IPPOC_PRODUCTION is set but IPPOC_API_KEY is missing"""
        os.environ["IPPOC_PRODUCTION"] = "true"
        if "IPPOC_API_KEY" in os.environ: del os.environ["IPPOC_API_KEY"]

        # This should raise SystemExit(1)
        with self.assertRaises(SystemExit) as cm:
             self.run_server_code()
        self.assertEqual(cm.exception.code, 1)

    def test_production_with_key_ok(self):
        """Test that server starts if IPPOC_PRODUCTION is set and IPPOC_API_KEY is present"""
        os.environ["IPPOC_PRODUCTION"] = "true"
        os.environ["IPPOC_API_KEY"] = "secure-key"

        try:
            self.run_server_code()
        except SystemExit:
            self.fail("Server exited unexpectedly with valid config")

    def test_dev_generates_key(self):
        """Test that server generates a key in dev mode if missing"""
        if "IPPOC_PRODUCTION" in os.environ: del os.environ["IPPOC_PRODUCTION"]
        if "IPPOC_API_KEY" in os.environ: del os.environ["IPPOC_API_KEY"]

        # We verify that secrets.token_hex was called (which means it generated a key)
        # Note: server.py imports secrets. Since we mocked sys.modules["secrets"],
        # but server.py does `import secrets`, it gets the mock.
        # But wait, I didn't mock `secrets` in the list above, only `uuid`.
        # server.py imports `secrets`. If I don't mock it, it uses real secrets.
        # Real secrets.token_hex works fine.
        # But to detect if it was called, I should mock it.

        with patch("secrets.token_hex", return_value="mocked_key") as mock_token:
            # We also need to mock print to avoid spamming stdout and check if it printed
            with patch("builtins.print") as mock_print:
                self.run_server_code()
                mock_token.assert_called()
                # Check if it printed the key
                # Note: This test expects current behavior (printing key in dev).
                # My fix will change it to print to stderr.
                # So I should check if it prints to stderr OR stdout for now.
                # Actually, I should check that it DOES log/print in dev.
                self.assertTrue(mock_print.called)

    def test_production_no_log_key(self):
        """Test that server DOES NOT log the key in production"""
        os.environ["IPPOC_PRODUCTION"] = "true"
        os.environ["IPPOC_API_KEY"] = "secure-key"

        with patch("builtins.print") as mock_print:
            self.run_server_code()
            # It shouldn't print the key warning because key is set
            # And it shouldn't print the key itself
            for call in mock_print.call_args_list:
                args, _ = call
                message = str(args[0])
                if "secure-key" in message:
                    self.fail("API Key leaked in logs!")

if __name__ == "__main__":
    unittest.main()
