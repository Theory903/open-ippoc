#!/usr/bin/env python3
"""Integration test script for Two-Tower Service gRPC API"""

import sys
import grpc
import time
import two_tower_pb2
import two_tower_pb2_grpc
from concurrent import futures

def test_grpc_service():
    """Test the gRPC service integration"""
    print("Testing Two-Tower Service gRPC integration...")
    
    # Connect to the service
    try:
        with grpc.insecure_channel('localhost:50051') as channel:
            stub = two_tower_pb2_grpc.TwoTowerServiceStub(channel)
            
            print("\n1. Testing ValidateAction RPC...")
            # Test 1: Low risk, high confidence action
            candidate1 = two_tower_pb2.ActionCandidate(
                action="safe_action",
                confidence=0.9,
                risk=two_tower_pb2.RiskLevel.LOW,
                payload={"key": "value"},
                requires_validation=True,
                trace_id="test_trace_123",
                timestamp=int(time.time())
            )
            
            decision1 = stub.ValidateAction(candidate1)
            print(f"   Action: {candidate1.action}")
            print(f"   Approved: {decision1.approved}")
            print(f"   Reason: {decision1.reason}")
            assert decision1.approved == True, "Low risk high confidence should be approved"
            
            # Test 2: High risk, low confidence action
            candidate2 = two_tower_pb2.ActionCandidate(
                action="risky_action",
                confidence=0.4,
                risk=two_tower_pb2.RiskLevel.CRITICAL,
                payload={"key": "value"},
                requires_validation=True,
                trace_id="test_trace_456",
                timestamp=int(time.time())
            )
            
            decision2 = stub.ValidateAction(candidate2)
            print(f"\n   Action: {candidate2.action}")
            print(f"   Approved: {decision2.approved}")
            print(f"   Reason: {decision2.reason}")
            assert decision2.approved == False, "High risk low confidence should be rejected"
            
            print("\n2. Testing BatchValidateActions RPC...")
            batch_request = two_tower_pb2.BatchValidationRequest(
                candidates=[candidate1, candidate2],
                trace_id="batch_test_789"
            )
            
            batch_response = stub.BatchValidateActions(batch_request)
            print(f"   Received {len(batch_response.decisions)} decisions")
            assert len(batch_response.decisions) == 2, "Should receive 2 decisions"
            
            print("\n3. Testing GetValidationStats RPC...")
            stats_request = two_tower_pb2.ValidationStatsRequest(
                start_time=0,
                end_time=int(time.time() + 3600)
            )
            
            stats_response = stub.GetValidationStats(stats_request)
            print(f"   Total requests: {stats_response.total_requests}")
            print(f"   Approved requests: {stats_response.approved_requests}")
            print(f"   Rejected requests: {stats_response.rejected_requests}")
            print(f"   Average validation time: {stats_response.avg_validation_time:.4f}s")
            print("   Risk distribution:")
            for entry in stats_response.risk_distribution:
                print(f"     {entry.key}: {entry.value}")
            
            assert stats_response.total_requests >= 2, "Should have at least 2 requests"
            
            print("\n✅ All gRPC service tests passed!")
            return True
            
    except grpc.RpcError as e:
        print(f"\n❌ gRPC connection error: {e.code()} - {e.details()}")
        if e.code() == grpc.StatusCode.UNAVAILABLE:
            print("   Is the Two-Tower service running on port 50051?")
        return False
    except Exception as e:
        print(f"\n❌ Error in gRPC service tests: {e}")
        import traceback
        print(traceback.format_exc())
        return False

def main():
    """Main test function"""
    try:
        success = test_grpc_service()
        if success:
            return 0
        else:
            return 1
    except Exception as e:
        print(f"\n❌ Error in main test: {e}")
        import traceback
        print(traceback.format_exc())
        return 1

if __name__ == "__main__":
    sys.exit(main())
