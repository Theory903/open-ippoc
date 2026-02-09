import unittest
from unittest.mock import MagicMock, patch, AsyncMock
import asyncio
from cortex.core.intents import Intent, IntentType
from cortex.core.autonomy import AutonomyController

class TestAutonomyLearning(unittest.TestCase):
    def setUp(self):
        self.patchers = []

        def start_patch(target, **kwargs):
            p = patch(target, **kwargs)
            m = p.start()
            self.patchers.append(p)
            return m

        self.mock_ledger = start_patch('cortex.core.autonomy.get_ledger')

        self.mock_orchestrator = MagicMock()
        self.mock_orchestrator.invoke_async = AsyncMock()
        start_patch('cortex.core.autonomy.get_orchestrator', return_value=self.mock_orchestrator)

        start_patch('cortex.core.autonomy.get_economy')
        start_patch('cortex.core.autonomy.collect_signals', new_callable=AsyncMock)
        start_patch('cortex.core.autonomy.get_evolver')
        start_patch('cortex.core.autonomy.get_hippocampus')
        start_patch('cortex.core.autonomy.get_trust_model')

        # Mock load/save state
        start_patch('cortex.core.autonomy.AutonomyController._load_state')
        start_patch('cortex.core.autonomy.AutonomyController._save_state')

        self.controller = AutonomyController()
        # Manually init skill_stats since we patched _load_state
        self.controller.skill_stats = {}

    def tearDown(self):
        for p in reversed(self.patchers):
            p.stop()

    def test_learn_insignificant(self):
        # 1st attempt, successful
        intent = Intent(description="test", priority=1.0, intent_type=IntentType.SERVE)
        evaluation = {"success": True}

        asyncio.run(self.controller.learn(intent, evaluation))

        # Check stats
        key = str(IntentType.SERVE)
        self.assertEqual(self.controller.skill_stats[key]["attempts"], 1)
        self.assertEqual(self.controller.skill_stats[key]["successes"], 1)

        # Check orchestrator NOT called (not significant yet, n=1 < 5)
        self.mock_orchestrator.invoke_async.assert_not_called()

    def test_learn_significant(self):
        intent = Intent(description="test", priority=1.0, intent_type=IntentType.SERVE)
        key = str(IntentType.SERVE)

        # Pre-populate stats to be just before threshold
        self.controller.skill_stats[key] = {"attempts": 4, "successes": 4} # 4/4 = 1.0

        evaluation = {"success": True}
        asyncio.run(self.controller.learn(intent, evaluation))

        # Now 5/5 = 1.0, n=5. Significant.
        self.assertEqual(self.controller.skill_stats[key]["attempts"], 5)
        self.assertEqual(self.controller.skill_stats[key]["successes"], 5)

        self.mock_orchestrator.invoke_async.assert_called_once()
        envelope = self.mock_orchestrator.invoke_async.call_args[0][0]
        self.assertEqual(envelope.action, "store_skill")
        self.assertEqual(envelope.context["skill"], key)

    def test_learn_low_success_rate(self):
        intent = Intent(description="test", priority=1.0, intent_type=IntentType.MAINTAIN)
        key = str(IntentType.MAINTAIN)

        # Pre-populate stats: 4 attempts, 1 success.
        self.controller.skill_stats[key] = {"attempts": 4, "successes": 1}

        # 5th attempt succeeds. Total 5 attempts, 2 successes. 2/5 = 0.4. Not > 0.6.
        evaluation = {"success": True}
        asyncio.run(self.controller.learn(intent, evaluation))

        self.assertEqual(self.controller.skill_stats[key]["attempts"], 5)
        self.assertEqual(self.controller.skill_stats[key]["successes"], 2)

        self.mock_orchestrator.invoke_async.assert_not_called()

    def test_learn_significant_but_failed_attempt(self):
        intent = Intent(description="test", priority=1.0, intent_type=IntentType.EXPLORE)
        key = str(IntentType.EXPLORE)

        # Pre-populate stats: 5 attempts, 5 successes.
        self.controller.skill_stats[key] = {"attempts": 5, "successes": 5}

        # 6th attempt fails. Total 6 attempts, 5 successes. 5/6 = 0.83 > 0.6. Significant.
        # BUT the attempt failed, so we shouldn't "learn" (record skill) based on a failure

        evaluation = {"success": False}
        asyncio.run(self.controller.learn(intent, evaluation))

        self.assertEqual(self.controller.skill_stats[key]["attempts"], 6)
        self.assertEqual(self.controller.skill_stats[key]["successes"], 5)

        self.mock_orchestrator.invoke_async.assert_not_called()

if __name__ == '__main__':
    unittest.main()
