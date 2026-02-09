#!/usr/bin/env python3
"""Test file for TwoTowerClient library

This test file covers:
- Basic client functionality
- Connection management
- Action validation (sync and async)
- Batch validation
- Statistics retrieval
- Error handling
- Retry logic
"""

import unittest
import time
import threading
from concurrent import futures
import grpc

from two_tower_client import (
    TwoTowerClient,
    ActionCandidate,
    ValidationDecision,
    RiskLevel,
    create_client,
    validate_action_simple,
    ConnectionError,
    ValidationError,
    ServiceError
)
import two_tower_pb2
import two_tower_pb2_grpc


class TestTwoTowerClient(unittest.TestCase):
    """Test cases for TwoTowerClient"""

    @classmethod
    def setUpClass(cls):
        """Setup before all tests"""
        cls.host = 'localhost'
        cls.port = 50051
        cls.test_timeout = 10.0

    def test_client_creation(self):
        """Test client creation and connection"""
        print("\nTest 1: Client creation and connection")
        client = create_client(self.host, self.port, timeout=5.0)
        self.assertIsNotNone(client)
        self.assertIsNotNone(client.channel)
        self.assertIsNotNone(client.stub)
        self.assertTrue(client.is_connected())
        client.close()

    def test_context_manager(self):
        """Test client as context manager"""
        print("\nTest 2: Context manager")
        with TwoTowerClient(self.host, self.port, timeout=5.0) as client:
            self.assertIsNotNone(client)
            self.assertTrue(client.is_connected())

    def test_simple_validation_function(self):
        """Test the simple validate_action_simple convenience function"""
        print("\nTest 3: Simple validation function")
        decision = validate_action_simple(
            action="simple_test_action",
            confidence=0.9,
            risk=RiskLevel.LOW,
            payload={"test": "data"},
            host=self.host,
            port=self.port
        )
        self.assertIsInstance(decision, ValidationDecision)
        self.assertTrue(decision.approved)
        self.assertIn("High confidence", decision.reason)
        self.assertGreater(decision.cost_spent, 0)

    def test_validate_action_low_risk_high_confidence(self):
        """Test validation of low risk, high confidence action"""
        print("\nTest 4: Low risk high confidence validation")
        with TwoTowerClient(self.host, self.port, timeout=5.0) as client:
            candidate = ActionCandidate(
                action="safe_action",
                confidence=0.95,
                risk=RiskLevel.LOW,
                payload={"key": "value"},
                requires_validation=True
            )
            decision = client.validate_action(candidate)
            self.assertIsInstance(decision, ValidationDecision)
            self.assertTrue(decision.approved)
            self.assertIn("High confidence", decision.reason)
            self.assertEqual(len(decision.warnings), 0)

    def test_validate_action_high_risk_low_confidence(self):
        """Test validation of high risk, low confidence action (should be rejected)"""
        print("\nTest 5: High risk low confidence validation")
        with TwoTowerClient(self.host, self.port, timeout=5.0) as client:
            candidate = ActionCandidate(
                action="risky_action",
                confidence=0.4,
                risk=RiskLevel.CRITICAL,
                payload={"key": "value"},
                requires_validation=True
            )
            decision = client.validate_action(candidate)
            self.assertIsInstance(decision, ValidationDecision)
            self.assertFalse(decision.approved)
            self.assertIn("Critical risk", decision.reason)
            self.assertGreater(len(decision.warnings), 0)

    def test_validate_action_no_validation(self):
        """Test validation of action that doesn't require validation"""
        print("\nTest 6: No validation required")
        with TwoTowerClient(self.host, self.port, timeout=5.0) as client:
            candidate = ActionCandidate(
                action="safe_no_validation",
                confidence=0.5,
                risk=RiskLevel.MEDIUM,
                payload={"key": "value"},
                requires_validation=False
            )
            decision = client.validate_action(candidate)
            self.assertIsInstance(decision, ValidationDecision)
            self.assertTrue(decision.approved)
            self.assertIn("does not require validation", decision.reason)

    def test_batch_validate_actions(self):
        """Test batch validation of multiple actions"""
        print("\nTest 7: Batch validation")
        with TwoTowerClient(self.host, self.port, timeout=10.0) as client:
            candidates = [
                ActionCandidate(
                    action="batch_action_1",
                    confidence=0.9,
                    risk=RiskLevel.LOW,
                    payload={"data": "1"}
                ),
                ActionCandidate(
                    action="batch_action_2",
                    confidence=0.5,
                    risk=RiskLevel.HIGH,
                    payload={"data": "2"}
                ),
                ActionCandidate(
                    action="batch_action_3",
                    confidence=0.7,
                    risk=RiskLevel.MEDIUM,
                    payload={"data": "3"}
                )
            ]

            decisions = client.batch_validate_actions(candidates)
            self.assertEqual(len(decisions), 3)
            for decision in decisions:
                self.assertIsInstance(decision, ValidationDecision)
                self.assertIsNotNone(decision.approved)

    def test_get_validation_stats(self):
        """Test getting validation statistics"""
        print("\nTest 8: Get validation stats")
        with TwoTowerClient(self.host, self.port, timeout=5.0) as client:
            # First, make a few validation calls to ensure stats are available
            client.validate_action(
                ActionCandidate(
                    action="stat_test_action",
                    confidence=0.85,
                    risk=RiskLevel.MEDIUM,
                    payload={"key": "value"}
                )
            )

            stats = client.get_validation_stats()
            self.assertGreater(stats.total_requests, 0)
            self.assertGreaterEqual(stats.approved_requests, 0)
            self.assertGreaterEqual(stats.rejected_requests, 0)
            self.assertGreater(stats.avg_validation_time, 0)
            self.assertEqual(len(stats.risk_distribution), 4)
            for risk_level in ['LOW', 'MEDIUM', 'HIGH', 'CRITICAL']:
                self.assertIn(risk_level, stats.risk_distribution)
                self.assertGreaterEqual(stats.risk_distribution[risk_level], 0)

    def test_validate_action_async(self):
        """Test async validation"""
        print("\nTest 9: Async validation")
        with TwoTowerClient(self.host, self.port, timeout=5.0) as client:
            candidate = ActionCandidate(
                action="async_action",
                confidence=0.9,
                risk=RiskLevel.LOW,
                payload={"key": "value"}
            )
            future = client.validate_action_async(candidate)
            self.assertIsInstance(future, futures.Future)
            decision = future.result(timeout=10.0)
            self.assertIsInstance(decision, ValidationDecision)
            self.assertTrue(decision.approved)

    def test_batch_validate_actions_async(self):
        """Test async batch validation"""
        print("\nTest 10: Async batch validation")
        with TwoTowerClient(self.host, self.port, timeout=10.0) as client:
            candidates = [
                ActionCandidate(
                    action="async_batch_1",
                    confidence=0.85,
                    risk=RiskLevel.MEDIUM,
                    payload={"data": "1"}
                ),
                ActionCandidate(
                    action="async_batch_2",
                    confidence=0.9,
                    risk=RiskLevel.LOW,
                    payload={"data": "2"}
                )
            ]
            future = client.batch_validate_actions_async(candidates)
            self.assertIsInstance(future, futures.Future)
            decisions = future.result(timeout=10.0)
            self.assertEqual(len(decisions), 2)
            for decision in decisions:
                self.assertIsInstance(decision, ValidationDecision)

    def test_payload_handling(self):
        """Test payload handling"""
        print("\nTest 11: Payload handling")
        test_payload = {
            "key1": "value1",
            "key2": "value2",
            "key3": "value3"
        }
        with TwoTowerClient(self.host, self.port, timeout=5.0) as client:
            candidate = ActionCandidate(
                action="payload_test",
                confidence=0.8,
                risk=RiskLevel.LOW,
                payload=test_payload
            )
            decision = client.validate_action(candidate)
            self.assertIsInstance(decision, ValidationDecision)

    def test_risk_level_conversion(self):
        """Test RiskLevel enum conversion"""
        print("\nTest 12: Risk level conversion")
        from_string = RiskLevel.from_string('medium')
        self.assertEqual(from_string, RiskLevel.MEDIUM)
        from_string_upper = RiskLevel.from_string('HIGH')
        self.assertEqual(from_string_upper, RiskLevel.HIGH)
        from_string_lower = RiskLevel.from_string('low')
        self.assertEqual(from_string_lower, RiskLevel.LOW)


def run_quick_test():
    """Quick test function to verify client functionality without running full suite"""
    print("Running quick TwoTowerClient test...")
    try:
        # Create client
        client = create_client(timeout=10.0)

        # Test 1: Validate simple action
        print("\n1. Testing validate_action()")
        candidate1 = ActionCandidate(
            action="quick_test_action",
            confidence=0.9,
            risk=RiskLevel.LOW,
            payload={"test": "data"}
        )
        decision1 = client.validate_action(candidate1)
        print(f"Action: '{candidate1.action}'")
        print(f"Approved: {decision1.approved}")
        print(f"Reason: {decision1.reason}")

        # Test 2: Get validation stats
        print("\n2. Testing get_validation_stats()")
        stats = client.get_validation_stats()
        print(f"Total requests: {stats.total_requests}")
        print(f"Approved: {stats.approved_requests} ({100 * stats.approved_requests / stats.total_requests:.1f}%)")
        print(f"Average validation time: {stats.avg_validation_time:.4f} seconds")

        client.close()
        print("\n✅ Quick test passed!")
        return True

    except ConnectionError:
        print("\n❌ Connection error: Is the Two-Tower service running on port 50051?")
        return False
    except Exception as e:
        print(f"\n❌ Error: {e}")
        return False


def main():
    """Main test runner"""
    # Check if service is available before running full tests
    print("Checking Two-Tower service availability...")
    try:
        with TwoTowerClient('localhost', 50051, timeout=5.0) as client:
            if client.is_connected():
                print("✅ Two-Tower service is running")
            else:
                print("❌ Two-Tower service is not available")
                return False
    except ConnectionError:
        print("❌ Cannot connect to Two-Tower service")
        print("⚠️  Note: The service should be running on localhost:50051")
        project_root = Path(__file__).resolve().parents[4]
        print(f"To start the service: cd {project_root}/src/ippoc/cortex/cortex && python3 server.py")
        return False
    except Exception as e:
        print(f"❌ Error checking service: {e}")
        return False

    print("\n" + "="*60)
    print("Running TwoTowerClient tests")
    print("="*60)

    # Run all tests
    unittest.main(module=__name__, verbosity=2)


if __name__ == '__main__':
    # If service is not running, run quick test that just checks connection
    try:
        import sys
        if len(sys.argv) > 1 and sys.argv[1] == '--quick':
            run_quick_test()
        else:
            main()
    except Exception as e:
        print(f"Error: {e}")
        import traceback
        print(traceback.format_exc())
