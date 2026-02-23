
import sys
import pytest
from unittest.mock import MagicMock
import types

def pytest_configure(config):
    """Mock heavy dependencies before tests are collected."""

    # Helper to create a package mock
    def mock_package(name):
        m = types.ModuleType(name)
        m.__path__ = []
        return m

    # Mock langchain_core
    if "langchain_core" not in sys.modules:
        langchain_core = mock_package("langchain_core")
        sys.modules["langchain_core"] = langchain_core

        # Mock langchain_core.documents
        documents = mock_package("langchain_core.documents")
        langchain_core.documents = documents
        sys.modules["langchain_core.documents"] = documents

        class Document:
            def __init__(self, page_content, metadata=None):
                self.page_content = page_content
                self.metadata = metadata or {}
        documents.Document = Document

        # Mock langchain_core.embeddings
        embeddings = mock_package("langchain_core.embeddings")
        langchain_core.embeddings = embeddings
        sys.modules["langchain_core.embeddings"] = embeddings
        embeddings.Embeddings = MagicMock()

        # Mock langchain_core.runnables
        runnables = mock_package("langchain_core.runnables")
        langchain_core.runnables = runnables
        sys.modules["langchain_core.runnables"] = runnables
        runnables.RunnablePassthrough = MagicMock()
        runnables.Runnable = MagicMock()

        # Mock langchain_core.output_parsers
        output_parsers = mock_package("langchain_core.output_parsers")
        langchain_core.output_parsers = output_parsers
        sys.modules["langchain_core.output_parsers"] = output_parsers
        output_parsers.StrOutputParser = MagicMock()

        # Mock langchain_core.prompts
        prompts = mock_package("langchain_core.prompts")
        langchain_core.prompts = prompts
        sys.modules["langchain_core.prompts"] = prompts
        prompts.PromptTemplate = MagicMock()

        # Mock langchain_core.language_models
        language_models = mock_package("langchain_core.language_models")
        langchain_core.language_models = language_models
        sys.modules["langchain_core.language_models"] = language_models
        language_models.BaseChatModel = MagicMock()

        # Mock langchain_core.vectorstores
        vectorstores = mock_package("langchain_core.vectorstores")
        langchain_core.vectorstores = vectorstores
        sys.modules["langchain_core.vectorstores"] = vectorstores
        vectorstores.VectorStore = MagicMock()

    # Mock langchain_community
    if "langchain_community" not in sys.modules:
        langchain_community = mock_package("langchain_community")
        sys.modules["langchain_community"] = langchain_community

        # Mock vectorstores
        lc_vectorstores = mock_package("langchain_community.vectorstores")
        langchain_community.vectorstores = lc_vectorstores
        sys.modules["langchain_community.vectorstores"] = lc_vectorstores
        lc_vectorstores.PGVector = MagicMock()

    # Mock pgvector
    if "pgvector" not in sys.modules:
        pgvector = mock_package("pgvector")
        sys.modules["pgvector"] = pgvector

        sqlalchemy = mock_package("pgvector.sqlalchemy")
        pgvector.sqlalchemy = sqlalchemy
        sys.modules["pgvector.sqlalchemy"] = sqlalchemy
        sqlalchemy.Vector = MagicMock()

    # Mock redis
    if "redis" not in sys.modules:
        redis = mock_package("redis")
        sys.modules["redis"] = redis
        redis.asyncio = MagicMock()
        sys.modules["redis.asyncio"] = redis.asyncio
