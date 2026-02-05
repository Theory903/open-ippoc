
import os
import json
import tempfile
import pytest
import shutil
from unittest.mock import patch
from cortex import explain

@pytest.fixture
def temp_explain_file():
    # Create a temporary directory
    temp_dir = tempfile.mkdtemp()
    file_path = os.path.join(temp_dir, "explain_test.json")

    # Patch the EXPLAIN_PATH in the module
    with patch("cortex.explain.EXPLAIN_PATH", file_path):
        yield file_path

    # Cleanup
    shutil.rmtree(temp_dir)

def test_log_decision_new_file(temp_explain_file):
    """Test logging to a new file creates JSONL."""
    explain.log_decision("action1", "reason1")

    assert os.path.exists(temp_explain_file)
    with open(temp_explain_file, "r") as f:
        lines = f.readlines()
        assert len(lines) == 1
        data = json.loads(lines[0])
        assert data["decision"]["action"] == "action1"

    # Log another
    explain.log_decision("action2", "reason2")
    with open(temp_explain_file, "r") as f:
        lines = f.readlines()
        assert len(lines) == 2
        data = json.loads(lines[1])
        assert data["decision"]["action"] == "action2"

def test_get_latest_explanation(temp_explain_file):
    """Test retrieving the latest explanation."""
    explain.log_decision("action1", "reason1")
    explain.log_decision("action2", "reason2")

    latest = explain.get_latest_explanation()
    assert latest is not None
    assert latest["decision"]["action"] == "action2"

def test_legacy_migration(temp_explain_file):
    """Test that existing JSON list file is migrated to JSONL."""
    # Create a legacy file
    legacy_data = [
        {"decision": {"action": "old1", "reason": "r1"}},
        {"decision": {"action": "old2", "reason": "r2"}}
    ]
    with open(temp_explain_file, "w") as f:
        json.dump(legacy_data, f)

    # Verify legacy format
    with open(temp_explain_file, "r") as f:
        content = f.read()
        assert content.startswith("[")

    # Log a new decision, should trigger migration
    explain.log_decision("new3", "r3")

    # Check format is now JSONL (lines)
    with open(temp_explain_file, "r") as f:
        lines = f.readlines()
        assert len(lines) == 3
        # First two should be from legacy
        assert json.loads(lines[0])["decision"]["action"] == "old1"
        assert json.loads(lines[1])["decision"]["action"] == "old2"
        # Third is new
        assert json.loads(lines[2])["decision"]["action"] == "new3"

    # Verify get_latest works
    latest = explain.get_latest_explanation()
    assert latest["decision"]["action"] == "new3"

def test_get_latest_legacy_fallback(temp_explain_file):
    """Test get_latest handles legacy file if for some reason it exists."""
    # This might happen if log_decision hasn't been called yet but we read
    legacy_data = [
        {"decision": {"action": "old1", "reason": "r1"}},
        {"decision": {"action": "old2", "reason": "r2"}}
    ]
    with open(temp_explain_file, "w") as f:
        json.dump(legacy_data, f)

    # Should be able to read it
    latest = explain.get_latest_explanation()
    assert latest["decision"]["action"] == "old2"
