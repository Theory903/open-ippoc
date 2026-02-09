# src/cortex/tests/test_independence_no_openclaw.py
import os
import sys
import unittest
import importlib
import pkgutil
from unittest.mock import MagicMock, patch

class TestIndependenceContract(unittest.TestCase):
    """
    NON-NEGOTIABLE CONTRACT TEST:
    Ensures IPPOC-OS can boot and register core tools even when 
    OpenClaw plugin code is strictly missing or inaccessible.
    """

    def setUp(self):
        # 1. Block the OpenClaw plugin modules in sys.modules
        # Setting a module to None in sys.modules forces an ImportError
        self.blocked_modules = {
            "ippoc.cortex.plugins.openclaw": None,
            "ippoc.cortex.plugins.openclaw.openclaw_adapter": None,
            "ippoc.cortex.plugins.openclaw.proprioception_scanner": None
        }
        self.module_patcher = patch.dict('sys.modules', self.blocked_modules)
        self.module_patcher.start()

    def tearDown(self):
        self.module_patcher.stop()

    def test_boot_without_openclaw(self):
        """Verify that bootstrap_tools completes without crashing when plugin is missing."""
        from ippoc.cortex.core.bootstrap import bootstrap_tools
        from ippoc.cortex.core.orchestrator import get_orchestrator
        
        # This should print [IPPOC] OpenClaw plugin not found, skipping synapse bridge to stderr
        # instead of raising ImportError.
        try:
            bootstrap_tools()
        except ImportError as e:
            self.fail(f"Independence Violation: bootstrap_tools failed due to missing plugin: {e}")
        except Exception as e:
            self.fail(f"Unexpected boot failure: {e}")

        orc = get_orchestrator()
        
        # Verify core tools are present
        self.assertIn("native_shell", orc.tools)
        self.assertIn("maintainer", orc.tools)
        
        # FINAL SOVEREIGNTY CHECK: Ensure no OpenClaw code was accidentally loaded
        violations = [mod_name for mod_name, mod in sys.modules.items() 
                      if "ippoc.cortex.plugins.openclaw" in mod_name and mod is not None]
        if violations:
            print(f"DEBUG: Found in sys.modules: {violations}", file=sys.stderr)
            self.fail(f"Hermetic Violation: {violations} were loaded during standalone boot!")

        # TRANSITIVE LEAKAGE CHECK: Scrape all available modules for "openclaw"
        leaked_pkg = []
        try:
            for _, name, _ in pkgutil.walk_packages(path=sys.path):
                # We allow modules inside the explicit plugins directory
                if "openclaw" in name.lower():
                    if not (name.startswith("ippoc.cortex.plugins.") or name.startswith("ippoc.plugins.openclaw") or "test_independence_no_openclaw" in name):
                         leaked_pkg.append(name)
        except Exception:
            # Some compiled modules might raise errors during walk_packages in certain envs
            pass
        
        self.assertEqual(len(leaked_pkg), 0, f"Independence Violation: Leaked OpenClaw-related packages found outside plugins: {leaked_pkg}")
        
        # Note: In our specific environment, we might find the plugin directory modules.
        # But we should NOT find anything that isn't isolated in plugins/
        
        # Verify OpenClaw skills are NOT present (since they require the scanner in the plugin)
        # Note: If they ARE present, it might mean the mock failed or they are hardcoded.
        registered_tools = list(orc.tools.keys())
        oc_skills = [t for t in registered_tools if t.startswith("openclaw_")]
        self.assertEqual(len(oc_skills), 0, f"Found OpenClaw skills despite missing plugin: {oc_skills}")
        
        print("✅ Independence Contract Test Passed: No structural dependency on OpenClaw.")

if __name__ == "__main__":
    unittest.main()
