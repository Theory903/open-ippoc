#!/usr/bin/env python3
"""
Test script to verify Ollama Kimi K2 Cloud LLM integration in IPPOC
"""

import sys
import os
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from src.cortex.cortex.two_tower import TwoTowerEngine
import asyncio

async def test_ollama_kimi_integration():
    """Test Ollama Kimi K2 Cloud integration"""
    print("🧪 Testing Ollama Kimi K2 Cloud integration...")
    
    # Create TwoTowerEngine instance
    engine = TwoTowerEngine()
    
    # Verify engine is initialized with Ollama
    if engine.provider != "ollama":
        print("❌ Engine not configured to use Ollama")
        return False
    
    # Verify LLM instances are created
    if engine.llm_a is None or engine.llm_b is None:
        print("❌ LLM instances not created")
        return False
    
    # Test generate_impulse
    print("   Testing Tower A (Impulse generation)...")
    context = "I want to learn about quantum computing. What are the basic concepts I should understand?"
    try:
        impulse = await engine.generate_impulse(context)
        print(f"   ✅ Success: {impulse}")
    except Exception as e:
        print(f"   ❌ Failed: {e}")
        return False
    
    # Test validate_action
    print("   Testing Tower B (Action validation)...")
    try:
        approved = await engine.validate_action(impulse)
        print(f"   ✅ Success: {'Approved' if approved else 'Rejected'}")
    except Exception as e:
        print(f"   ❌ Failed: {e}")
        return False
    
    # Verify model market contains Kimi models
    print("   Testing model market...")
    kimi_models = [model for model in engine.model_market.keys() if "kimi" in model.lower()]
    if len(kimi_models) == 0:
        print("❌ No Kimi models found in model market")
        return False
    
    print(f"   ✅ Success: Found {len(kimi_models)} Kimi models in model market")
    
    return True

async def main():
    """Main test function"""
    print("🚀 Starting Ollama Kimi K2 Cloud Integration Test")
    
    # Check if Ollama is running
    try:
        import subprocess
        result = subprocess.run(["ollama", "list"], capture_output=True, text=True)
        if result.returncode != 0:
            print("❌ Ollama is not running. Please start Ollama service first.")
            return
    except FileNotFoundError:
        print("❌ Ollama CLI not found. Please install Ollama first.")
        return
    
    # Pull Kimi model if not installed
    print("📦 Checking if Kimi K2.5 Cloud model is installed...")
    try:
        import subprocess
        result = subprocess.run(["ollama", "list"], capture_output=True, text=True)
        if "kimi-k2.5:cloud" not in result.stdout:
            print("   Downloading Kimi K2.5 Cloud model...")
            pull_result = subprocess.run(["ollama", "run", "kimi-k2.5:cloud"], check=True, capture_output=True, text=True)
            print(f"   ✅ Download complete: {pull_result.stdout}")
        else:
            print("   ✅ Kimi K2.5 Cloud model is already installed")
    except Exception as e:
        print(f"❌ Failed to check/install Kimi model: {e}")
        return
    
    # Run integration test
    success = await test_ollama_kimi_integration()
    
    if success:
        print("\n🎉 Ollama Kimi K2 Cloud integration test passed!")
    else:
        print("\n🚨 Ollama Kimi K2 Cloud integration test failed!")

if __name__ == "__main__":
    asyncio.run(main())
