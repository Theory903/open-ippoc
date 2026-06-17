import sys
import os
import unittest

# Add src to sys.path to ensure we can import the module
# Current file is src/tests/security/test_soma_api_key.py
# We need to add 'src' to path.
# dirname -> src/tests/security
# .. -> src/tests
# .. -> src
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "../..")))

from ippoc.soma.server import issue_api_key, verify_api_key, api_keys

class TestSomaApiKey(unittest.TestCase):
    def setUp(self):
        # Clear existing keys for clean test
        api_keys.clear()

    def test_api_key_generation_and_verification(self):
        # Generate a key
        result = issue_api_key(node_id="test-node")
        api_key = result["api_key"]

        # Verify structure
        self.assertEqual(result["status"], "success")
        self.assertEqual(result["node_id"], "test-node")

        # Verify key properties
        self.assertIsInstance(api_key, str)
        # token_urlsafe(32) produces ~43 characters (32 bytes * 4/3 base64 overhead)
        self.assertGreaterEqual(len(api_key), 40)
        self.assertIn(api_key, api_keys)

        # Verify the key works
        verify_result = verify_api_key(api_key)
        self.assertEqual(verify_result["status"], "valid")
        self.assertEqual(verify_result["node_id"], "test-node")

        # Verify uniqueness
        result2 = issue_api_key(node_id="test-node-2")
        api_key2 = result2["api_key"]
        self.assertNotEqual(api_key, api_key2)
        self.assertEqual(len(api_keys), 2)

if __name__ == "__main__":
    unittest.main()
