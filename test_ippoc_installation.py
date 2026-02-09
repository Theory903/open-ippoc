#!/usr/bin/env python3
"""
IPPOC v1.0.0 Installation & Verification Test
This script tests the isolated installation and verification of resulting ~/.ippoc structure.
"""

import os
import shutil
import subprocess
import time
import requests
from pathlib import Path

def test_isolated_installation():
    """Test that install.sh creates the correct structure in ~/.ippoc"""
    print("🧪 Testing IPPOC installation...")
    
    # Cleanup existing installation
    ippoc_home = Path.home() / ".ippoc"
    if ippoc_home.exists():
        print(f"   Removing existing installation at {ippoc_home}")
        shutil.rmtree(ippoc_home)
    
    # Run installation
    print("   Running install.sh...")
    result = subprocess.run(["./install.sh"], check=True, capture_output=True, text=True)
    print(f"   Installation output:\n{result.stdout}")
    
    # Verify installation structure
    print("   Verifying installation structure...")
    assert ippoc_home.exists()
    assert (ippoc_home / "venv").exists()
    assert (ippoc_home / "instances" / "main" / "data").exists()
    assert (ippoc_home / "instances" / "main" / "logs").exists()
    
    # Verify CLI shim
    bin_dir = Path.home() / ".local" / "bin"
    assert (bin_dir / "ippoc").exists()
    assert os.access(bin_dir / "ippoc", os.X_OK)
    
    print("✅ Installation test passed!")

def test_cli_basic_commands():
    """Test basic CLI commands"""
    print("🧪 Testing CLI commands...")
    
    # Test ippoc --help
    result = subprocess.run(["ippoc", "--help"], check=True, capture_output=True, text=True)
    assert "IPPOC Universal Platform CLI" in result.stdout
    
    # Test ippoc setup
    result = subprocess.run(["ippoc", "setup"], check=True, capture_output=True, text=True)
    assert "Instance 'main' verified" in result.stdout
    
    print("✅ CLI commands test passed!")

def test_cognitive_stream():
    """Test the cognitive stream endpoint"""
    print("🧪 Testing cognitive stream endpoint...")
    
    # Start services in background
    print("   Starting IPPOC services...")
    process = subprocess.Popen(["ippoc", "run"], stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True)
    
    # Wait for services to start
    time.sleep(30)
    
    try:
        # Check if Cortex is alive and responding
        response = requests.get("http://localhost:8000/readyz", timeout=5)
        assert response.status_code == 200
        
        # Check cognitive stream
        response = requests.get("http://localhost:8000/v1/cognitive/stream", timeout=5)
        assert response.status_code == 200
        
        print("✅ Cognitive stream test passed!")
    finally:
        # Stop services
        process.terminate()
        try:
            process.wait(timeout=10)
        except subprocess.TimeoutExpired:
            process.kill()

def test_capability_violations():
    """Test CAP-01 violations"""
    print("🧪 Testing CAP-01 violations...")
    
    # TODO: Implement test for capability violations
    print("⚠️  CAP-01 violation test not implemented yet")

if __name__ == "__main__":
    print("🚀 Starting IPPOC v1.0.0 Verification...")
    
    tests = [
        test_isolated_installation,
        test_cli_basic_commands,
        # test_cognitive_stream,  # Requires running services, which may fail in CI
        # test_capability_violations
    ]
    
    passed = 0
    failed = 0
    
    for test in tests:
        try:
            test()
            passed += 1
        except Exception as e:
            print(f"❌ Test failed: {e}")
            failed += 1
            import traceback
            print(traceback.format_exc())
    
    print(f"\n📊 Test Results: {passed} passed, {failed} failed")
    
    if failed > 0:
        sys.exit(1)
