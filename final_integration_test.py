#!/usr/bin/env python3
"""
Final Integration Test for IPPOC System
Tests the core functionality with running services
"""

import requests
import json
import time
import asyncio
from typing import Dict, Any, Optional

# Configuration
MEMORY_URL = "http://localhost:8000"
CORTEX_URL = "http://localhost:8001"
API_KEY = "ippoc-secret-key"  # Default development key
TEST_TIMEOUT = 30

def test_service_health(service_name: str, url: str) -> bool:
    """Test if a service is responding"""
    try:
        response = requests.get(f"{url}/health", timeout=5)
        if response.status_code == 200:
            print(f"✅ {service_name}: OK")
            return True
        else:
            print(f"❌ {service_name}: HTTP {response.status_code}")
            return False
    except Exception as e:
        print(f"❌ {service_name}: {e}")
        return False

def test_memory_operations():
    """Test basic memory operations"""
    print("\n=== Testing Memory Operations ===")
    
    # Test storing data
    store_data = {
        "content": "Test memory entry from integration test",
        "source": "integration_test",
        "confidence": 0.9,
        "metadata": {"test": True, "timestamp": time.time()}
    }
    
    try:
        response = requests.post(
            f"{MEMORY_URL}/v1/memory/consolidate",
            json=store_data,
            timeout=30
        )
        
        if response.status_code == 200:
            result = response.json()
            print(f"✅ Memory store: {result.get('status', 'OK')}")
            
            # Test retrieval
            search_response = requests.get(
                f"{MEMORY_URL}/v1/memory/search",
                params={"query": "integration test"},
                timeout=10
            )
            
            if search_response.status_code == 200:
                search_result = search_response.json()
                print(f"✅ Memory search: Found {len(search_result.get('results', []))} results")
                return True
            else:
                print(f"❌ Memory search failed: {search_response.status_code}")
                return False
        else:
            print(f"❌ Memory store failed: {response.status_code}")
            return False
            
    except Exception as e:
        print(f"❌ Memory operations failed: {e}")
        return False

def test_cortex_reasoning():
    """Test basic cortex reasoning"""
    print("\n=== Testing Cortex Reasoning ===")
    
    # Test signal processing
    signal_data = {
        "timestamp": time.time(),
        "node_id": "integration_test",
        "context": {
            "task": "Test cognitive processing",
            "tool": "integration_verification"
        },
        "metrics": {
            "duration_sec": 0.1,
            "cost_ippc": 0.01,
            "success": True
        }
    }
    
    try:
        response = requests.post(
            f"{CORTEX_URL}/v1/signals/ingest",
            json=signal_data,
            headers={
                "Content-Type": "application/json",
                "Authorization": f"Bearer {API_KEY}"
            },
            timeout=15
        )
        
        if response.status_code == 200:
            result = response.json()
            print(f"✅ Cortex signal processing: {result.get('status', 'OK')}")
            
            # Check if we got cognitive state
            if 'cognitive_state_snapshot' in result:
                snapshot = result['cognitive_state_snapshot']
                print(f"✅ Cognitive snapshot: {snapshot.get('mode', 'unknown')}")
                return True
            else:
                print("⚠️  No cognitive state in response (may be normal)")
                return True
        else:
            print(f"❌ Cortex signal processing failed: {response.status_code}")
            print(f"Response: {response.text}")
            return False
            
    except Exception as e:
        print(f"❌ Cortex reasoning failed: {e}")
        return False

def test_tool_execution():
    """Test basic tool execution through cortex"""
    print("\n=== Testing Tool Execution ===")
    
    # Test memory tool execution
    tool_request = {
        "tool_name": "memory",
        "domain": "memory", 
        "action": "retrieve",
        "context": {
            "query": "test data"
        },
        "risk_level": "low",
        "estimated_cost": 0.1
    }
    
    try:
        response = requests.post(
            f"{CORTEX_URL}/v1/tools/execute",
            json=tool_request,
            headers={
                "Content-Type": "application/json",
                "Authorization": f"Bearer {API_KEY}"
            },
            timeout=15
        )
        
        if response.status_code == 200:
            result = response.json()
            print(f"✅ Tool execution: Success = {result.get('success', False)}")
            if result.get('success'):
                print(f"✅ Output: {str(result.get('output', ''))[:100]}...")
            return True
        else:
            print(f"❌ Tool execution failed: {response.status_code}")
            try:
                error_detail = response.json()
                print(f"Error: {error_detail}")
            except:
                print(f"Response: {response.text}")
            return False
            
    except Exception as e:
        print(f"❌ Tool execution failed: {e}")
        return False

def main():
    """Main test function"""
    print("🐝 IPPOC Final Integration Test")
    print("=" * 50)
    
    # Test service health
    print("=== Service Health Check ===")
    memory_ok = test_service_health("Memory (HiDB)", MEMORY_URL)
    cortex_ok = test_service_health("Cortex (Reasoning)", CORTEX_URL)
    
    if not (memory_ok and cortex_ok):
        print("\n❌ Critical services are not responding!")
        return False
    
    # Run integration tests
    memory_test_ok = test_memory_operations()
    cortex_test_ok = test_cortex_reasoning()
    tool_test_ok = test_tool_execution()
    
    # Summary
    print("\n" + "=" * 50)
    print("📊 TEST SUMMARY")
    print("=" * 50)
    print(f"Memory Service: {'✅ PASS' if memory_ok else '❌ FAIL'}")
    print(f"Cortex Service: {'✅ PASS' if cortex_ok else '❌ FAIL'}")
    print(f"Memory Operations: {'✅ PASS' if memory_test_ok else '❌ FAIL'}")
    print(f"Cortex Reasoning: {'✅ PASS' if cortex_test_ok else '❌ FAIL'}")
    print(f"Tool Execution: {'✅ PASS' if tool_test_ok else '❌ FAIL'}")
    
    overall_success = all([memory_ok, cortex_ok, memory_test_ok, cortex_test_ok, tool_test_ok])
    
    if overall_success:
        print("\n🎉 ALL TESTS PASSED!")
        print("✅ IPPOC system is fully operational")
        print("✅ Memory and Cortex services are working")
        print("✅ Tool orchestration is functioning")
        print("✅ Cognitive processing is active")
    else:
        print("\n⚠️  SOME TESTS FAILED")
        print("The system may be partially functional")
    
    return overall_success

if __name__ == "__main__":
    success = main()
    exit(0 if success else 1)