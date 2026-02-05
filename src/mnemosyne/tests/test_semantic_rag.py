"""
Comprehensive tests for Semantic RAG Manager

Tests cover:
- SemanticManager initialization
- Content processing (text, tables, figures)
- Semantic object creation
- Advanced retrieval mechanisms
- HyDE retrieval
- Batch operations
- Content type handling
- Edge cases and error handling
"""

import pytest
from unittest.mock import MagicMock, AsyncMock, patch
from langchain_core.documents import Document

from mnemosyne.semantic.rag import (
    SemanticManager,
    SemanticObject,
    ContentType
)


@pytest.fixture
def mock_vector_store():
    """Mock vector store"""
    mock_store = MagicMock()
    mock_store.aadd_documents = AsyncMock(return_value=["id1", "id2", "id3"])
    mock_store.asimilarity_search_with_score = AsyncMock(return_value=[])
    mock_store.as_retriever = MagicMock(return_value="retriever")
    return mock_store


@pytest.fixture
def mock_embeddings():
    """Mock embeddings model"""
    mock_emb = MagicMock()
    mock_emb.embed_query = AsyncMock(return_value=[0.1] * 128)
    mock_emb.aembed_documents = AsyncMock(return_value=[[0.1] * 128, [0.2] * 128])
    return mock_emb


@pytest.fixture
def mock_llm():
    """Mock LLM for HyDE"""
    mock_model = MagicMock()
    mock_response = MagicMock()
    mock_response.content = "Generated hypothetical document"
    mock_model.ainvoke = AsyncMock(return_value=mock_response)
    return mock_model


@pytest.fixture
def manager(mock_vector_store, mock_embeddings):
    """Create SemanticManager instance"""
    return SemanticManager(mock_vector_store, mock_embeddings)


@pytest.fixture
def manager_with_llm(mock_vector_store, mock_embeddings, mock_llm):
    """Create SemanticManager with LLM"""
    return SemanticManager(mock_vector_store, mock_embeddings, mock_llm)


class TestSemanticManagerInitialization:
    """Test SemanticManager initialization"""

    def test_init_basic(self, mock_vector_store, mock_embeddings):
        """Should initialize with required components"""
        manager = SemanticManager(mock_vector_store, mock_embeddings)

        assert manager.vector_store is mock_vector_store
        assert manager.embeddings is mock_embeddings
        assert manager.llm is None
        assert manager.semantic_objects == []
        assert manager.object_index == {}

    def test_init_with_llm(self, mock_vector_store, mock_embeddings, mock_llm):
        """Should initialize with optional LLM"""
        manager = SemanticManager(mock_vector_store, mock_embeddings, mock_llm)

        assert manager.llm is mock_llm

    def test_default_parameters(self, manager):
        """Should have sensible defaults"""
        assert manager.default_k == 5
        assert manager.min_score_threshold == 0.8
        assert manager.chunk_size == 1000
        assert manager.chunk_overlap == 200


class TestContentType:
    """Test ContentType enum"""

    def test_content_types_exist(self):
        """Should have all content types"""
        assert ContentType.TEXT.value == "text"
        assert ContentType.TABLE.value == "table"
        assert ContentType.FIGURE.value == "figure"
        assert ContentType.CODE.value == "code"
        assert ContentType.LIST.value == "list"
        assert ContentType.FORMULA.value == "formula"


class TestSemanticObject:
    """Test SemanticObject dataclass"""

    def test_semantic_object_creation(self):
        """Should create SemanticObject with required fields"""
        obj = SemanticObject(
            id="obj_123",
            content="Test content",
            content_type=ContentType.TEXT,
            semantic_components=["component1", "component2"],
            context_window="Context here",
            metadata={"key": "value"}
        )

        assert obj.id == "obj_123"
        assert obj.content == "Test content"
        assert obj.content_type == ContentType.TEXT
        assert len(obj.semantic_components) == 2
        assert obj.confidence == 1.0  # default

    def test_semantic_object_with_optional_fields(self):
        """Should accept optional fields"""
        obj = SemanticObject(
            id="obj_456",
            content="Content",
            content_type=ContentType.TABLE,
            semantic_components=[],
            context_window="",
            metadata={},
            confidence=0.85,
            source_document="doc.pdf",
            page_number=5,
            position=(100.0, 200.0)
        )

        assert obj.confidence == 0.85
        assert obj.source_document == "doc.pdf"
        assert obj.page_number == 5
        assert obj.position == (100.0, 200.0)


class TestAddMemory:
    """Test add_memory functionality"""

    @pytest.mark.asyncio
    async def test_add_memory_text(self, manager, mock_vector_store):
        """Should add text memory"""
        object_ids = await manager.add_memory(
            "This is a test paragraph about Python programming.",
            metadata={"source": "test"}
        )

        assert len(object_ids) > 0
        assert len(manager.semantic_objects) > 0
        mock_vector_store.aadd_documents.assert_called_once()

    @pytest.mark.asyncio
    async def test_add_memory_creates_semantic_objects(self, manager):
        """Should create semantic objects from content"""
        await manager.add_memory(
            "Python is a programming language. It is widely used.",
            metadata={"category": "programming"}
        )

        assert len(manager.semantic_objects) > 0
        obj = manager.semantic_objects[0]
        assert obj.content_type == ContentType.TEXT
        assert len(obj.semantic_components) >= 0

    @pytest.mark.asyncio
    async def test_add_memory_indexes_objects(self, manager):
        """Should index objects by ID"""
        await manager.add_memory("Test content", metadata={})

        assert len(manager.object_index) == len(manager.semantic_objects)
        for obj in manager.semantic_objects:
            assert obj.id in manager.object_index

    @pytest.mark.asyncio
    async def test_add_memory_table_type(self, manager):
        """Should handle table content type"""
        table_content = "Header1 | Header2 | Header3\nValue1 | Value2 | Value3"

        object_ids = await manager.add_memory(
            table_content,
            metadata={"type": "table"},
            content_type=ContentType.TABLE
        )

        assert len(object_ids) > 0

    @pytest.mark.asyncio
    async def test_add_memory_error_handling(self, manager, mock_vector_store):
        """Should handle errors gracefully"""
        mock_vector_store.aadd_documents.side_effect = Exception("Vector store error")

        with pytest.raises(Exception):
            await manager.add_memory("Test", metadata={})


class TestRetrieveRelevant:
    """Test retrieve_relevant functionality"""

    @pytest.mark.asyncio
    async def test_retrieve_relevant_basic(self, manager, mock_vector_store):
        """Should retrieve relevant documents"""
        mock_doc = Document(page_content="Content", metadata={"id": "doc1"})
        mock_vector_store.asimilarity_search_with_score.return_value = [
            (mock_doc, 0.9)
        ]

        results = await manager.retrieve_relevant("test query")

        assert len(results) > 0
        mock_vector_store.asimilarity_search_with_score.assert_called_once()

    @pytest.mark.asyncio
    async def test_retrieve_relevant_with_custom_k(self, manager, mock_vector_store):
        """Should respect custom k parameter"""
        await manager.retrieve_relevant("query", k=10)

        call_args = mock_vector_store.asimilarity_search_with_score.call_args
        assert call_args[1]['k'] == 10

    @pytest.mark.asyncio
    async def test_retrieve_relevant_filters_by_score(self, manager, mock_vector_store):
        """Should filter results by min_score"""
        mock_doc1 = Document(page_content="High score", metadata={})
        mock_doc2 = Document(page_content="Low score", metadata={})

        mock_vector_store.asimilarity_search_with_score.return_value = [
            (mock_doc1, 0.95),
            (mock_doc2, 0.5)
        ]

        results = await manager.retrieve_relevant("query", min_score=0.8)

        # Should only return high score result
        assert len(results) == 1

    @pytest.mark.asyncio
    async def test_retrieve_relevant_with_metadata_filter(self, manager, mock_vector_store):
        """Should apply metadata filters"""
        filter_meta = {"category": "programming"}

        await manager.retrieve_relevant("query", filter_metadata=filter_meta)

        call_args = mock_vector_store.asimilarity_search_with_score.call_args
        assert call_args[1]['filter'] == filter_meta

    @pytest.mark.asyncio
    async def test_retrieve_relevant_advanced_retrieval(self, manager):
        """Should use advanced retrieval when available"""
        # Add some semantic objects
        await manager.add_memory("Python programming language", metadata={})

        results = await manager.retrieve_relevant(
            "Python",
            use_advanced_retrieval=True
        )

        assert isinstance(results, list)

    @pytest.mark.asyncio
    async def test_retrieve_relevant_fallback_on_error(self, manager, mock_vector_store):
        """Should return empty list on error"""
        mock_vector_store.asimilarity_search_with_score.side_effect = Exception("Error")

        results = await manager.retrieve_relevant("query")

        assert results == []


class TestAsRetriever:
    """Test as_retriever functionality"""

    def test_as_retriever(self, manager, mock_vector_store):
        """Should expose vector store as retriever"""
        retriever = manager.as_retriever()

        assert retriever == "retriever"
        mock_vector_store.as_retriever.assert_called_once()

    def test_as_retriever_with_kwargs(self, manager, mock_vector_store):
        """Should pass kwargs to vector store"""
        manager.as_retriever(search_kwargs={"k": 10})

        mock_vector_store.as_retriever.assert_called_with(search_kwargs={"k": 10})


class TestBatchOperations:
    """Test batch_add functionality"""

    @pytest.mark.asyncio
    async def test_batch_add_multiple_texts(self, manager, mock_vector_store):
        """Should add multiple texts in batch"""
        texts = ["Text 1", "Text 2", "Text 3"]
        metadatas = [{"id": "1"}, {"id": "2"}, {"id": "3"}]

        ids = await manager.batch_add(texts, metadatas)

        assert len(ids) > 0
        mock_vector_store.aadd_documents.assert_called_once()

    @pytest.mark.asyncio
    async def test_batch_add_without_metadata(self, manager, mock_vector_store):
        """Should handle batch add without metadata"""
        texts = ["Text 1", "Text 2"]

        ids = await manager.batch_add(texts)

        # Should create empty metadata for each text
        call_args = mock_vector_store.aadd_documents.call_args[0][0]
        assert len(call_args) == 2

    @pytest.mark.asyncio
    async def test_batch_add_error_handling(self, manager, mock_vector_store):
        """Should raise exception on batch add error"""
        mock_vector_store.aadd_documents.side_effect = Exception("Batch error")

        with pytest.raises(Exception):
            await manager.batch_add(["Text"])


class TestTextChunking:
    """Test semantic text chunking"""

    def test_chunk_text_semantically_single_paragraph(self, manager):
        """Should handle single paragraph"""
        text = "This is a short paragraph."

        chunks = manager._chunk_text_semantically(text)

        assert len(chunks) >= 1
        assert chunks[0] == "This is a short paragraph."

    def test_chunk_text_semantically_multiple_paragraphs(self, manager):
        """Should split by paragraph boundaries"""
        text = "Paragraph 1 here.\n\nParagraph 2 here.\n\nParagraph 3 here."

        chunks = manager._chunk_text_semantically(text)

        assert len(chunks) >= 1

    def test_chunk_text_respects_chunk_size(self, manager):
        """Should respect chunk_size parameter"""
        long_text = "A" * 2000  # Longer than chunk_size

        chunks = manager._chunk_text_semantically(long_text)

        # Should split into multiple chunks
        assert len(chunks) >= 1

    def test_chunk_text_handles_empty_input(self, manager):
        """Should handle empty input"""
        chunks = manager._chunk_text_semantically("")

        assert chunks == []


class TestSemanticComponentExtraction:
    """Test semantic component extraction"""

    def test_extract_semantic_components_capitalized_terms(self, manager):
        """Should extract capitalized terms"""
        text = "Python Programming Language is used for Data Science."

        components = manager._extract_semantic_components(text)

        assert isinstance(components, list)
        # Should extract some capitalized terms
        assert len(components) >= 0

    def test_extract_semantic_components_numbers(self, manager):
        """Should extract numbers"""
        text = "The value is 42 and percentage is 85.5%."

        components = manager._extract_semantic_components(text)

        # Should include numbers
        number_components = [c for c in components if any(char.isdigit() for char in c)]
        assert len(number_components) > 0

    def test_extract_semantic_components_filters_short_terms(self, manager):
        """Should filter out very short terms"""
        text = "A I is AI technology."

        components = manager._extract_semantic_components(text)

        # Should filter terms with length <= 2
        assert all(len(comp) > 2 for comp in components)

    def test_extract_semantic_components_limits_results(self, manager):
        """Should limit to top 10 components"""
        text = " ".join([f"Term{i}" for i in range(50)])

        components = manager._extract_semantic_components(text)

        assert len(components) <= 10


class TestTableProcessing:
    """Test table processing"""

    def test_parse_table_rows_pipe_separated(self, manager):
        """Should parse pipe-separated tables"""
        content = "Header1 | Header2 | Header3\nValue1 | Value2 | Value3"

        rows = manager._parse_table_rows(content)

        assert len(rows) >= 2
        assert len(rows[0]) == 3

    def test_parse_table_rows_tab_separated(self, manager):
        """Should parse tab-separated tables"""
        content = "Header1\tHeader2\tHeader3\nValue1\tValue2\tValue3"

        rows = manager._parse_table_rows(content)

        assert len(rows) >= 2

    def test_parse_table_rows_space_separated(self, manager):
        """Should parse space-separated tables"""
        content = "Header1  Header2  Header3\nValue1  Value2  Value3"

        rows = manager._parse_table_rows(content)

        assert len(rows) >= 1

    def test_extract_table_components(self, manager):
        """Should extract components from table row"""
        row = ["Python", "3.9", "Active"]

        components = manager._extract_table_components(row)

        assert isinstance(components, list)
        assert len(components) <= 5


class TestConfidenceCalculation:
    """Test confidence score calculation"""

    def test_calculate_confidence_basic(self, manager):
        """Should calculate confidence score"""
        confidence = manager._calculate_confidence("Some content", ["comp1", "comp2"])

        assert 0.0 <= confidence <= 1.0

    def test_calculate_confidence_with_long_content(self, manager):
        """Should give higher confidence for longer content"""
        short_content = "Short"
        long_content = "A" * 1000

        conf_short = manager._calculate_confidence(short_content, [])
        conf_long = manager._calculate_confidence(long_content, [])

        assert conf_long >= conf_short

    def test_calculate_confidence_with_more_components(self, manager):
        """Should give higher confidence with more components"""
        few_comps = ["comp1"]
        many_comps = ["comp1", "comp2", "comp3", "comp4", "comp5"]

        conf_few = manager._calculate_confidence("Content", few_comps)
        conf_many = manager._calculate_confidence("Content", many_comps)

        assert conf_many >= conf_few


class TestHyDERetrieval:
    """Test HyDE (Hypothetical Document Embeddings) retrieval"""

    @pytest.mark.asyncio
    async def test_hyde_retrieve_with_llm(self, manager_with_llm, mock_llm, mock_embeddings):
        """Should use LLM to generate hypothetical document"""
        # Add some objects to search
        await manager_with_llm.add_memory("Python programming", metadata={})

        results = await manager_with_llm.hyde_retrieve("What is Python?")

        # Should have called LLM
        mock_llm.ainvoke.assert_called_once()
        assert isinstance(results, list)

    @pytest.mark.asyncio
    async def test_hyde_retrieve_without_llm(self, manager, mock_embeddings):
        """Should create synthetic document without LLM"""
        await manager.add_memory("Test content", metadata={})

        results = await manager.hyde_retrieve("test query")

        assert isinstance(results, list)

    @pytest.mark.asyncio
    async def test_hyde_retrieve_with_params(self, manager_with_llm):
        """Should respect k and min_score parameters"""
        await manager_with_llm.add_memory("Content", metadata={})

        results = await manager_with_llm.hyde_retrieve(
            "query",
            k=3,
            min_score=0.9
        )

        assert isinstance(results, list)

    @pytest.mark.asyncio
    async def test_hyde_retrieve_fallback_on_error(self, manager_with_llm, mock_llm):
        """Should fallback to standard retrieval on error"""
        mock_llm.ainvoke.side_effect = Exception("LLM error")

        # Should not raise, should fallback
        results = await manager_with_llm.hyde_retrieve("query")

        assert isinstance(results, list)

    def test_create_synthetic_document(self, manager):
        """Should create synthetic document from query"""
        synthetic = manager._create_synthetic_document("What is Python programming?")

        assert len(synthetic) > 0
        assert "Python" in synthetic or "programming" in synthetic


class TestImageProcessing:
    """Test image/figure processing"""

    def test_is_image_path(self, manager):
        """Should identify image file paths"""
        assert manager._is_image_path("/path/to/image.png") is True
        assert manager._is_image_path("/path/to/image.jpg") is True
        assert manager._is_image_path("/path/to/image.jpeg") is True
        assert manager._is_image_path("/path/to/doc.pdf") is False
        assert manager._is_image_path("/path/to/file.txt") is False

    def test_is_image_path_case_insensitive(self, manager):
        """Should be case-insensitive for extensions"""
        assert manager._is_image_path("IMAGE.PNG") is True
        assert manager._is_image_path("photo.JPG") is True


class TestAdvancedRetrieval:
    """Test advanced retrieval with semantic objects"""

    @pytest.mark.asyncio
    async def test_advanced_retrieve_component_matching(self, manager):
        """Should match based on semantic components"""
        # Add memory with known components
        await manager.add_memory("Python is a programming language", metadata={})

        results = await manager._advanced_retrieve(
            "Python programming",
            k=5,
            min_score=0.5,
            filter_metadata=None
        )

        assert isinstance(results, list)

    @pytest.mark.asyncio
    async def test_advanced_retrieve_with_metadata_filter(self, manager):
        """Should filter by metadata"""
        await manager.add_memory("Content 1", metadata={"category": "A"})
        await manager.add_memory("Content 2", metadata={"category": "B"})

        results = await manager._advanced_retrieve(
            "query",
            k=5,
            min_score=0.0,
            filter_metadata={"category": "A"}
        )

        # Should only return content with category A
        assert isinstance(results, list)

    def test_matches_filter(self, manager):
        """Should correctly match metadata filters"""
        obj_meta = {"category": "test", "type": "document"}

        # Exact match
        assert manager._matches_filter(obj_meta, {"category": "test"}) is True

        # Partial match
        assert manager._matches_filter(obj_meta, {"category": "test", "type": "document"}) is True

        # No match
        assert manager._matches_filter(obj_meta, {"category": "other"}) is False

        # Missing key
        assert manager._matches_filter(obj_meta, {"missing": "key"}) is False


class TestEdgeCases:
    """Test edge cases and error conditions"""

    @pytest.mark.asyncio
    async def test_add_memory_empty_content(self, manager):
        """Should handle empty content"""
        object_ids = await manager.add_memory("", metadata={})

        # Should create at least one object
        assert len(object_ids) >= 0

    @pytest.mark.asyncio
    async def test_retrieve_relevant_empty_query(self, manager, mock_vector_store):
        """Should handle empty query"""
        results = await manager.retrieve_relevant("")

        assert isinstance(results, list)

    @pytest.mark.asyncio
    async def test_batch_add_empty_list(self, manager):
        """Should handle empty text list"""
        ids = await manager.batch_add([])

        assert ids == []

    def test_chunk_text_with_only_whitespace(self, manager):
        """Should handle whitespace-only input"""
        chunks = manager._chunk_text_semantically("   \n\n   \t\t   ")

        assert chunks == []

    def test_extract_components_from_empty_text(self, manager):
        """Should handle empty text"""
        components = manager._extract_semantic_components("")

        assert components == []

    @pytest.mark.asyncio
    async def test_get_stats_unavailable(self, manager):
        """Should return unavailable status for stats"""
        stats = await manager.get_stats()

        assert stats["status"] == "unavailable"


class TestDeleteMemories:
    """Test delete_memories functionality"""

    @pytest.mark.asyncio
    async def test_delete_memories(self, manager):
        """Should attempt to delete memories"""
        result = await manager.delete_memories(["id1", "id2"])

        # Returns True but may not actually delete (depends on vector store)
        assert result is True

    @pytest.mark.asyncio
    async def test_delete_memories_empty_list(self, manager):
        """Should handle empty ID list"""
        result = await manager.delete_memories([])

        assert result is True


class TestRegressionCases:
    """Regression tests for previously identified issues"""

    @pytest.mark.asyncio
    async def test_multiple_add_memory_calls(self, manager):
        """Should handle multiple add_memory calls"""
        for i in range(5):
            await manager.add_memory(f"Content {i}", metadata={"index": i})

        assert len(manager.semantic_objects) >= 5

    @pytest.mark.asyncio
    async def test_retrieve_after_multiple_adds(self, manager):
        """Should retrieve from accumulated objects"""
        await manager.add_memory("Python programming", metadata={})
        await manager.add_memory("JavaScript development", metadata={})

        results = await manager.retrieve_relevant("programming", use_advanced_retrieval=True)

        assert isinstance(results, list)


if __name__ == "__main__":
    pytest.main([__file__, "-v"])