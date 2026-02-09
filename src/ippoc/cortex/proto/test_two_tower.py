#!/usr/bin/env python3
"""Test script to verify Two-Tower Bridge Python bindings

Note: For integration testing of the gRPC service, use test_two_tower_service.py
which requires the TwoTower service to be running on port 50051.
"""

import sys
import grpc
import two_tower_pb2
import two_tower_pb2_grpc

def test_generate_bindings():
    """Test if we can import the generated modules and create basic messages"""
    print("Testing Python bindings import...")
    
    # Test creating ActionCandidate
    candidate = two_tower_pb2.ActionCandidate(
        action="test_action",
        confidence=0.85,
        risk=two_tower_pb2.RiskLevel.MEDIUM,
        payload={"key": "value"},
        requires_validation=True,
        trace_id="test_trace_123",
        timestamp=1234567890
    )
    
    print("✓ ActionCandidate created successfully")
    print(f"  Action: {candidate.action}")
    print(f"  Confidence: {candidate.confidence}")
    print(f"  Risk Level: {two_tower_pb2.RiskLevel.Name(candidate.risk)}")
    
    # Test creating ValidationDecision
    decision = two_tower_pb2.ValidationDecision(
        approved=True,
        reason="Test approval",
        cost_spent=0.1,
        warnings=["Test warning"],
        trace_id="test_trace_123",
        timestamp=1234567900
    )
    
    print("\n✓ ValidationDecision created successfully")
    print(f"  Approved: {decision.approved}")
    print(f"  Reason: {decision.reason}")
    print(f"  Cost Spent: {decision.cost_spent}")
    
    # Test enumerating risk levels
    print("\n✓ RiskLevel enum values:")
    for name, value in two_tower_pb2.RiskLevel.items():
        if name != " RiskLevel" and not name.startswith("_"):
            print(f"  {name}: {value}")
    
    return True

def main():
    """Main test function"""
    try:
        success = test_generate_bindings()
        if success:
            print("\n✅ All Python binding tests passed!")
            return 0
        else:
            print("\n❌ Some Python binding tests failed!")
            return 1
    except Exception as e:
        print(f"\n❌ Error in Python binding tests: {e}")
        import traceback
        print(traceback.format_exc())
        return 1

if __name__ == "__main__":
    sys.exit(main())
