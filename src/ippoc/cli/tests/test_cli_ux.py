import sys
import io
from unittest.mock import patch, MagicMock
from src.ippoc.cli.main import colorize, print_services_status

def test_colorize_tty():
    with patch('sys.stdout.isatty', return_value=True):
        assert colorize("test", "green") == "\033[92mtest\033[0m"
        assert colorize("test", "red") == "\033[91mtest\033[0m"
        assert colorize("test", "bold") == "\033[1mtest\033[0m"

def test_colorize_no_tty():
    with patch('sys.stdout.isatty', return_value=False):
        assert colorize("test", "green") == "test"

def test_print_services_status_colors():
    # Mock get_all_services_status
    mock_services = {
        "soma": {"port": 8081, "pid": 1234, "running": True, "healthy": True},
        "cortex": {"port": 8001, "pid": None, "running": False, "healthy": False},
    }

    with patch('src.ippoc.cli.main.get_all_services_status', return_value=mock_services), \
         patch('sys.stdout.isatty', return_value=True), \
         patch('sys.stdout', new_callable=io.StringIO) as fake_out:

        # We need to mock sys.stdout on the module level if print uses it directly?
        # print() writes to sys.stdout by default.
        # But patching sys.stdout globally works for print().
        # However, isatty must be mocked on the original stdout or the mocked one.
        # Here we mock sys.stdout.isatty separately.

        # Note: mocking sys.stdout replaces the object. The mocked object needs isatty method if code calls it on sys.stdout directly.
        # But our code calls sys.stdout.isatty().
        # If we replace sys.stdout with StringIO, StringIO doesn't have isatty returning True by default.

        # Let's adjust the patch.
        # The code imports sys. So sys.stdout is accessed.

        # If we patch sys.stdout with StringIO, we need to ensure the colorize function (which calls sys.stdout.isatty()) works.
        # Wait, colorize calls `sys.stdout.isatty()`.
        # If we patch `sys.stdout`, then `sys.stdout` is the mock object.
        # We can set `sys.stdout.isatty` on the mock.

        fake_out.isatty = MagicMock(return_value=True)

        print_services_status()
        output = fake_out.getvalue()

        # Check for green "Running" and "✓"
        assert "\033[92m🟢 Running\033[0m" in output
        assert "\033[92m✓\033[0m" in output

        # Check for red "Stopped" and "✗"
        assert "\033[91m🔴 Stopped\033[0m" in output
        assert "\033[91m✗\033[0m" in output

        # Check for bold service names
        assert "\033[1mSOMA    \033[0m" in output
        assert "\033[1mCORTEX  \033[0m" in output
