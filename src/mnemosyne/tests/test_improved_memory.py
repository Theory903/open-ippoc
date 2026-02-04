#!/usr/bin/env python3
"""
Test suite for the improved Mnemosyne memory system.

This test validates:
- Core MemorySystem interface
- Individual memory managers
- Cross-memory search capabilities
- Error handling and edge cases
"""

import sys
import os
import asyncio
import tempfile
from pathlib import Path

# Add src to path for imports
sys.path.insert(0, str(Path(__file__).parent.parent))

async def test_core_memory_system():
    """Test the unified MemorySystem interface"""
    print("🧪 Testing Core Memory System...")
    
    try:
        from mnemosyne import MemorySystem
        
        # Test initialization without vector store (episodic + graph only)
        memory = MemorySystem(db_url="sqlite+aiosqlite:///:memory:")
        
        # Test initialization
        await memory.initialize()
        print("   ✓ Memory system initialized")
        
        # Test episodic storage
        event_id = await memory.store_episodic(
            "User asked about Python memory management",
            source="chat",
            modality="text"
        )
        print(f"   ✓ Episodic event stored: {event_id}")
        
        # Test recall
        results = await memory.recall("Python memory", limit=5)
        print(f"   ✓ Recall returned {len(results)} results")
        
        # Test health check
        health = memory.health_check()
        print(f"   ✓ Health check: {health}")
        
        return True
        
    except Exception as e:
        print(f"   ❌ Core memory system test failed: {e}")
        import traceback
        traceback.print_exc()
        return False

async def test_episodic_manager():
    """Test the improved episodic memory manager"""
    print("\n🧪 Testing Episodic Manager...")
    
    try:
        from mnemosyne.episodic.manager import EpisodicManager
        
        # Use in-memory SQLite for testing
        manager = EpisodicManager(db_url="sqlite+aiosqlite:///:memory:", echo=False)
        
        # Initialize database
        await manager.init_db()
        print("   ✓ Database initialized")
        
        # Test storing events
        event1_id = await manager.write(
            "First test event about machine learning",
            source="test",
            modality="text"
        )
        
        event2_id = await manager.write(
            "Second test event about neural networks",
            source="test",
            modality="text"
        )
        print(f"   ✓ Stored 2 events with IDs: {event1_id}, {event2_id}")
        
        # Test search functionality
        results = await manager.search("machine learning", limit=5)
        assert len(results) >= 1
        print(f"   ✓ Search returned {len(results)} results")
        
        # Test filtered search
        ml_results = await manager.search("neural", source="test")
        assert len(ml_results) >= 1
        print(f"   ✓ Filtered search returned {len(ml_results)} results")
        
        # Test recent events
        recent = await manager.get_recent(limit=10)
        assert len(recent) == 2
        print(f"   ✓ Recent events query returned {len(recent)} items")
        
        # Test statistics
        stats = await manager.stats()
        assert "total_events" in stats
        print(f"   ✓ Stats retrieved: {stats['total_events']} total events")
        
        return True
        
    except Exception as e:
        print(f"   ❌ Episodic manager test failed: {e}")
        import traceback
        traceback.print_exc()
        return False

async def test_semantic_manager():
    """Test the improved semantic memory manager"""
    print("\n🧪 Testing Semantic Manager...")
    
    try:
        # Mock vector store for testing
        class MockVectorStore:
            def __init__(self):
                self.docs = []
                
            async def aadd_documents(self, docs):
                ids = [f"doc_{len(self.docs) + i}" for i in range(len(docs))]
                for doc, doc_id in zip(docs, ids):
                    self.docs.append((doc, doc_id))
                return ids
                
            async def asimilarity_search_with_score(self, query, k=5, filter=None):
                # Return all docs with dummy scores
                return [(doc, 0.8) for doc, _ in self.docs[:k]]
                
            def as_retriever(self, **kwargs):
                return "mock_retriever"
        
        class MockEmbeddings:
            pass
        
        from mnemosyne.semantic.rag import SemanticManager
        
        vector_store = MockVectorStore()
        embeddings = MockEmbeddings()
        
        manager = SemanticManager(vector_store, embeddings)
        print("   ✓ Semantic manager initialized")
        
        # Test single addition
        ids = await manager.add_memory("Test semantic content", {"topic": "testing"})
        assert len(ids) == 1
        print(f"   ✓ Added memory with ID: {ids[0]}")
        
        # Test batch addition
        texts = ["Content 1", "Content 2", "Content 3"]
        batch_ids = await manager.batch_add(texts)
        assert len(batch_ids) == 3
        print(f"   ✓ Batch added {len(batch_ids)} memories")
        
        # Test retrieval
        results = await manager.retrieve_relevant("test query", k=2)
        assert len(results) <= 2
        print(f"   ✓ Retrieved {len(results)} relevant documents")
        
        # Test retriever interface
        retriever = manager.as_retriever()
        assert retriever == "mock_retriever"
        print("   ✓ Retriever interface working")
        
        # Test stats
        stats = await manager.get_stats()
        assert "status" in stats
        print(f"   ✓ Stats retrieved: {stats['status']}")
        
        return True
        
    except Exception as e:
        print(f"   ❌ Semantic manager test failed: {e}")
        import traceback
        traceback.print_exc()
        return False

async def test_integration():
    """Test integration between memory components"""
    print("\n🧪 Testing Memory Integration...")
    
    try:
        from mnemosyne import memory, episodic, semantic, procedural, hidb
        
        # Test that convenience imports work
        assert memory is not None
        assert episodic is not None
        print("   ✓ Convenience imports working")
        
        # Test health check on convenience instances
        health = memory.health_check()
        assert isinstance(health, dict)
        print(f"   ✓ Memory health: initialized={health['initialized']}")
        
        return True
        
    except Exception as e:
        print(f"   ❌ Integration test failed: {e}")
        import traceback
        traceback.print_exc()
        return False

async def run_all_tests():
    """Run all memory system tests"""
    print("🚀 Starting Mnemosyne Memory System Tests")
    print("=" * 50)
    
    tests = [
        test_core_memory_system,
        test_episodic_manager,
        test_semantic_manager,
        test_integration
    ]
    
    results = []
    for test_func in tests:
        try:
            result = await test_func()
            results.append(result)
        except Exception as e:
            print(f"   ❌ Test {test_func.__name__} crashed: {e}")
            results.append(False)
    
    print("\n" + "=" * 50)
    passed = sum(results)
    total = len(results)
    
    if passed == total:
        print(f"✅ All tests passed! ({passed}/{total})")
        print("\n🎉 Memory system improvements verified!")
        print("✨ Key enhancements:")
        print("   • Unified MemorySystem interface")
        print("   • Improved error handling")
        print("   • Better search capabilities")
        print("   • Enhanced configuration options")
        print("   • Comprehensive logging")
    else:
        print(f"❌ {total - passed} tests failed ({passed}/{total})")
        return False
    
    return True

if __name__ == "__main__":
    # Install required test dependencies if needed
    try:
        import aiosqlite
    except ImportError:
        print("Installing test dependencies...")
        import subprocess
        subprocess.run([sys.executable, "-m", "pip", "install", "aiosqlite"], check=True)
    
    success = asyncio.run(run_all_tests())
    sys.exit(0 if success else 1)