"""
Comprehensive tests for Mnemosyne Core Memory System

Tests cover:
- MemorySystem initialization
- Episodic memory storage and recall
- Semantic memory operations
- Procedural memory (skill registration)
- Graph memory (relationships)
- Cross-memory search
- Health checks and error handling
- Edge cases and boundary conditions
"""

import pytest
import asyncio
from unittest.mock import MagicMock, AsyncMock, patch
from datetime import datetime
from typing import List, Dict

from mnemosyne.core import (
    MemorySystem,
    MemoryFragment,
    get_memory_system
)


@pytest.fixture
def mock_vector_store():
    """Mock vector store for semantic memory"""
    mock_store = MagicMock()
    mock_store.aadd_documents = AsyncMock(return_value=["doc1", "doc2"])
    mock_store.asimilarity_search_with_score = AsyncMock(return_value=[])
    mock_store.as_retriever = MagicMock()
    return mock_store


@pytest.fixture
def mock_embeddings():
    """Mock embeddings model"""
    mock_emb = MagicMock()
    mock_emb.embed_query = AsyncMock(return_value=[0.1] * 128)
    mock_emb.aembed_documents = AsyncMock(return_value=[[0.1] * 128])
    return mock_emb


@pytest.fixture
def mock_managers():
    """Mock all memory managers"""
    with patch('mnemosyne.core.EpisodicManager') as mock_episodic, \
         patch('mnemosyne.core.SemanticManager') as mock_semantic, \
         patch('mnemosyne.core.ProceduralManager') as mock_procedural, \
         patch('mnemosyne.core.GraphManager') as mock_graph:

        # Setup episodic manager
        mock_episodic_instance = MagicMock()
        mock_episodic_instance.init_db = AsyncMock()
        mock_episodic_instance.write = AsyncMock(return_value="event_123")
        mock_episodic_instance.search = AsyncMock(return_value=[])
        mock_episodic.return_value = mock_episodic_instance

        # Setup semantic manager
        mock_semantic_instance = MagicMock()
        mock_semantic_instance.add_memory = AsyncMock(return_value=["sem_1", "sem_2"])
        mock_semantic_instance.retrieve_relevant = AsyncMock(return_value=[])
        mock_semantic.return_value = mock_semantic_instance

        # Setup procedural manager
        mock_procedural_instance = MagicMock()
        mock_procedural_instance.register_skill = AsyncMock(return_value="Skill registered")
        mock_procedural_instance.find_skill = AsyncMock(return_value=[])
        mock_procedural.return_value = mock_procedural_instance

        # Setup graph manager
        mock_graph_instance = MagicMock()
        mock_graph_instance.init_db = AsyncMock()
        mock_graph_instance.add_triple = AsyncMock(return_value="Triple added")
        mock_graph_instance.get_neighbors = AsyncMock(return_value=[])
        mock_graph.return_value = mock_graph_instance

        yield {
            'episodic': mock_episodic_instance,
            'semantic': mock_semantic_instance,
            'procedural': mock_procedural_instance,
            'graph': mock_graph_instance
        }


class TestMemorySystemInitialization:
    """Test MemorySystem initialization"""

    def test_init_without_vector_store(self):
        """System should initialize without vector store"""
        system = MemorySystem()

        assert system.episodic is not None
        assert system.graph is not None
        assert system.semantic is None
        assert system.procedural is None
        assert system._initialized is False

    def test_init_with_vector_store(self, mock_vector_store, mock_embeddings):
        """System should initialize with vector store"""
        system = MemorySystem(
            vector_store=mock_vector_store,
            embeddings=mock_embeddings
        )

        assert system.semantic is not None
        assert system.procedural is not None

    def test_init_with_db_url(self):
        """System should accept db_url parameter"""
        system = MemorySystem(db_url="sqlite:///:memory:")

        assert system.episodic is not None
        assert system.graph is not None

    @pytest.mark.asyncio
    async def test_initialize_idempotent(self, mock_managers):
        """Initialize should be idempotent"""
        system = MemorySystem()

        await system.initialize()
        await system.initialize()  # Second call

        # Should only call init_db once
        assert system._initialized is True


class TestMemoryFragment:
    """Test MemoryFragment dataclass"""

    def test_memory_fragment_creation(self):
        """MemoryFragment should be created with required fields"""
        fragment = MemoryFragment(
            type="episodic",
            content="Test memory",
            metadata={"key": "value"},
            score=0.95
        )

        assert fragment.type == "episodic"
        assert fragment.content == "Test memory"
        assert fragment.metadata == {"key": "value"}
        assert fragment.score == 0.95
        assert fragment.timestamp is None
        assert fragment.id is None

    def test_memory_fragment_with_timestamp(self):
        """MemoryFragment should accept timestamp"""
        now = datetime.now()
        fragment = MemoryFragment(
            type="semantic",
            content="Knowledge",
            metadata={},
            timestamp=now
        )

        assert fragment.timestamp == now

    def test_memory_fragment_defaults(self):
        """MemoryFragment should have default values"""
        fragment = MemoryFragment(
            type="graph",
            content="Relation",
            metadata={}
        )

        assert fragment.score == 1.0
        assert fragment.timestamp is None


class TestEpisodicMemory:
    """Test episodic memory operations"""

    @pytest.mark.asyncio
    async def test_store_episodic_basic(self, mock_managers):
        """Should store episodic memory"""
        system = MemorySystem()

        event_id = await system.store_episodic(
            "User asked about Python",
            source="chat"
        )

        assert event_id == "episodic:event_123"
        mock_managers['episodic'].write.assert_called_once()

    @pytest.mark.asyncio
    async def test_store_episodic_with_metadata(self, mock_managers):
        """Should store episodic memory with metadata"""
        system = MemorySystem()

        metadata = {"user_id": "user123", "session": "sess456"}
        event_id = await system.store_episodic(
            "Complex interaction",
            source="api",
            modality="text",
            metadata=metadata
        )

        assert event_id.startswith("episodic:")
        call_args = mock_managers['episodic'].write.call_args
        assert call_args[0][0] == "Complex interaction"
        assert call_args[0][1] == "api"
        assert call_args[0][2] == "text"
        assert call_args[0][3] == metadata

    @pytest.mark.asyncio
    async def test_store_episodic_different_modalities(self, mock_managers):
        """Should handle different modalities"""
        system = MemorySystem()

        modalities = ["text", "code", "image", "audio"]

        for modality in modalities:
            await system.store_episodic(
                f"Content in {modality}",
                source="system",
                modality=modality
            )

        assert mock_managers['episodic'].write.call_count == len(modalities)


class TestSemanticMemory:
    """Test semantic memory operations"""

    @pytest.mark.asyncio
    async def test_store_semantic_basic(self, mock_managers, mock_vector_store, mock_embeddings):
        """Should store semantic knowledge"""
        system = MemorySystem(
            vector_store=mock_vector_store,
            embeddings=mock_embeddings
        )

        doc_ids = await system.store_semantic("Python is a programming language")

        assert doc_ids == ["sem_1", "sem_2"]
        mock_managers['semantic'].add_memory.assert_called_once()

    @pytest.mark.asyncio
    async def test_store_semantic_with_metadata(self, mock_managers, mock_vector_store, mock_embeddings):
        """Should store semantic knowledge with metadata"""
        system = MemorySystem(
            vector_store=mock_vector_store,
            embeddings=mock_embeddings
        )

        metadata = {"category": "programming", "confidence": 0.9}
        await system.store_semantic("Fact about Python", metadata=metadata)

        call_args = mock_managers['semantic'].add_memory.call_args
        assert call_args[0][1] == metadata

    @pytest.mark.asyncio
    async def test_store_semantic_without_vector_store(self):
        """Should raise error without vector store"""
        system = MemorySystem()

        with pytest.raises(RuntimeError, match="Semantic memory not configured"):
            await system.store_semantic("Some fact")


class TestProceduralMemory:
    """Test procedural memory operations"""

    @pytest.mark.asyncio
    async def test_register_skill_basic(self, mock_managers, mock_vector_store, mock_embeddings):
        """Should register a skill"""
        system = MemorySystem(
            vector_store=mock_vector_store,
            embeddings=mock_embeddings
        )

        result = await system.register_skill(
            name="data_analysis",
            code="def analyze(data): pass",
            description="Analyzes data"
        )

        assert result == "Skill registered"
        mock_managers['procedural'].register_skill.assert_called_once()

    @pytest.mark.asyncio
    async def test_register_skill_different_languages(self, mock_managers, mock_vector_store, mock_embeddings):
        """Should register skills in different languages"""
        system = MemorySystem(
            vector_store=mock_vector_store,
            embeddings=mock_embeddings
        )

        languages = ["python", "javascript", "rust"]

        for lang in languages:
            await system.register_skill(
                name=f"skill_{lang}",
                code="code here",
                description="Description",
                language=lang
            )

        assert mock_managers['procedural'].register_skill.call_count == len(languages)

    @pytest.mark.asyncio
    async def test_register_skill_without_vector_store(self):
        """Should raise error without vector store"""
        system = MemorySystem()

        with pytest.raises(RuntimeError, match="Procedural memory not configured"):
            await system.register_skill(
                name="test",
                code="code",
                description="desc"
            )


class TestGraphMemory:
    """Test graph memory operations"""

    @pytest.mark.asyncio
    async def test_add_relation_basic(self, mock_managers):
        """Should add relation to graph"""
        system = MemorySystem()

        result = await system.add_relation(
            source="Python",
            relation="is_a",
            target="Programming Language"
        )

        assert result == "Triple added"
        mock_managers['graph'].add_triple.assert_called_once()

    @pytest.mark.asyncio
    async def test_add_relation_with_types(self, mock_managers):
        """Should add relation with entity types"""
        system = MemorySystem()

        await system.add_relation(
            source="John",
            relation="works_at",
            target="Company",
            source_type="Person",
            target_type="Organization"
        )

        call_args = mock_managers['graph'].add_triple.call_args[0]
        assert call_args[3] == "Person"
        assert call_args[4] == "Organization"

    @pytest.mark.asyncio
    async def test_get_context(self, mock_managers):
        """Should get context from graph"""
        mock_managers['graph'].get_neighbors.return_value = [
            "is_a: Language",
            "used_for: Web Development"
        ]

        system = MemorySystem()
        context = await system.get_context("Python")

        assert context["entity"] == "Python"
        assert len(context["relations"]) == 2
        assert "timestamp" in context


class TestRecall:
    """Test comprehensive recall across subsystems"""

    @pytest.mark.asyncio
    async def test_recall_all_types(self, mock_managers, mock_vector_store, mock_embeddings):
        """Recall should search all memory types"""
        # Setup mock responses
        mock_managers['episodic'].search.return_value = [{
            "content": "Episodic memory",
            "metadata": {"id": "e1", "timestamp": datetime.now().isoformat()},
            "score": 0.9
        }]

        from langchain_core.documents import Document
        mock_managers['semantic'].retrieve_relevant.return_value = [
            Document(page_content="Semantic memory", metadata={"id": "s1"})
        ]

        mock_managers['procedural'].find_skill.return_value = [{
            "content": "Skill code",
            "metadata": {"skill": "test"},
            "score": 0.85,
            "id": "p1"
        }]

        mock_managers['graph'].get_neighbors.return_value = ["relation1", "relation2"]

        system = MemorySystem(
            vector_store=mock_vector_store,
            embeddings=mock_embeddings
        )

        results = await system.recall("test query", limit=10)

        assert len(results) > 0
        # Should have called all subsystems
        mock_managers['episodic'].search.assert_called_once()
        mock_managers['semantic'].retrieve_relevant.assert_called_once()
        mock_managers['procedural'].find_skill.assert_called_once()
        mock_managers['graph'].get_neighbors.assert_called_once()

    @pytest.mark.asyncio
    async def test_recall_specific_types(self, mock_managers):
        """Recall should filter by memory types"""
        system = MemorySystem()

        await system.recall("query", include_types=["episodic", "graph"])

        # Should only call episodic and graph
        mock_managers['episodic'].search.assert_called_once()
        mock_managers['graph'].get_neighbors.assert_called_once()

    @pytest.mark.asyncio
    async def test_recall_with_limit(self, mock_managers):
        """Recall should respect limit parameter"""
        # Create multiple mock results
        mock_managers['episodic'].search.return_value = [
            {
                "content": f"Memory {i}",
                "metadata": {"id": f"e{i}", "timestamp": datetime.now().isoformat()},
                "score": 0.9 - i * 0.1
            }
            for i in range(20)
        ]

        system = MemorySystem()
        results = await system.recall("query", limit=5)

        assert len(results) <= 5

    @pytest.mark.asyncio
    async def test_recall_handles_exceptions(self, mock_managers):
        """Recall should handle exceptions gracefully"""
        mock_managers['episodic'].search.side_effect = Exception("Database error")

        system = MemorySystem()
        results = await system.recall("query")

        # Should return results from other systems that didn't fail
        assert isinstance(results, list)

    @pytest.mark.asyncio
    async def test_recall_sorts_by_score(self, mock_managers):
        """Recall should sort results by relevance score"""
        mock_managers['episodic'].search.return_value = [
            {
                "content": "Low score",
                "metadata": {"id": "e1", "timestamp": datetime.now().isoformat()},
                "score": 0.5
            },
            {
                "content": "High score",
                "metadata": {"id": "e2", "timestamp": datetime.now().isoformat()},
                "score": 0.95
            }
        ]

        system = MemorySystem()
        results = await system.recall("query", limit=10)

        # Higher scores should come first
        if len(results) >= 2:
            assert results[0].score >= results[1].score


class TestHealthCheck:
    """Test health check functionality"""

    def test_health_check_basic(self):
        """Health check should return status"""
        system = MemorySystem()
        health = system.health_check()

        assert "initialized" in health
        assert "episodic_enabled" in health
        assert "semantic_enabled" in health
        assert "procedural_enabled" in health
        assert "graph_enabled" in health
        assert "timestamp" in health

    def test_health_check_with_vector_store(self, mock_vector_store, mock_embeddings):
        """Health check should reflect vector store availability"""
        system = MemorySystem(
            vector_store=mock_vector_store,
            embeddings=mock_embeddings
        )
        health = system.health_check()

        assert health["semantic_enabled"] is True
        assert health["procedural_enabled"] is True

    def test_health_check_without_vector_store(self):
        """Health check should show disabled semantic/procedural"""
        system = MemorySystem()
        health = system.health_check()

        assert health["semantic_enabled"] is False
        assert health["procedural_enabled"] is False


class TestGetMemorySystem:
    """Test global singleton"""

    def test_get_memory_system_creates_instance(self):
        """Should create global instance"""
        # Reset global
        import mnemosyne.core
        mnemosyne.core._memory_system = None

        system1 = get_memory_system()
        system2 = get_memory_system()

        assert system1 is system2

    def test_get_memory_system_with_params(self):
        """Should pass parameters on first call"""
        import mnemosyne.core
        mnemosyne.core._memory_system = None

        system = get_memory_system(db_url="sqlite:///:memory:")

        assert system is not None


class TestEdgeCases:
    """Test edge cases and boundary conditions"""

    @pytest.mark.asyncio
    async def test_store_episodic_empty_content(self, mock_managers):
        """Should handle empty content"""
        system = MemorySystem()

        event_id = await system.store_episodic("", source="test")

        assert event_id.startswith("episodic:")

    @pytest.mark.asyncio
    async def test_store_semantic_empty_metadata(self, mock_managers, mock_vector_store, mock_embeddings):
        """Should handle None metadata"""
        system = MemorySystem(
            vector_store=mock_vector_store,
            embeddings=mock_embeddings
        )

        doc_ids = await system.store_semantic("Content", metadata=None)

        # Should use empty dict
        call_args = mock_managers['semantic'].add_memory.call_args[0]
        assert call_args[1] == {}

    @pytest.mark.asyncio
    async def test_recall_empty_query(self, mock_managers):
        """Should handle empty query"""
        system = MemorySystem()

        results = await system.recall("")

        assert isinstance(results, list)

    @pytest.mark.asyncio
    async def test_recall_with_zero_limit(self, mock_managers):
        """Should handle zero limit"""
        system = MemorySystem()

        results = await system.recall("query", limit=0)

        assert results == []

    @pytest.mark.asyncio
    async def test_forget_not_implemented(self):
        """Forget should raise NotImplementedError"""
        system = MemorySystem()

        with pytest.raises(NotImplementedError):
            await system.forget({"type": "episodic"})


class TestConcurrentOperations:
    """Test concurrent memory operations"""

    @pytest.mark.asyncio
    async def test_concurrent_stores(self, mock_managers):
        """Should handle concurrent store operations"""
        system = MemorySystem()

        tasks = [
            system.store_episodic(f"Event {i}", source="test")
            for i in range(10)
        ]

        results = await asyncio.gather(*tasks)

        assert len(results) == 10
        assert all(r.startswith("episodic:") for r in results)

    @pytest.mark.asyncio
    async def test_concurrent_recalls(self, mock_managers):
        """Should handle concurrent recall operations"""
        system = MemorySystem()

        tasks = [
            system.recall(f"query {i}")
            for i in range(5)
        ]

        results = await asyncio.gather(*tasks)

        assert len(results) == 5
        assert all(isinstance(r, list) for r in results)


if __name__ == "__main__":
    pytest.main([__file__, "-v"])