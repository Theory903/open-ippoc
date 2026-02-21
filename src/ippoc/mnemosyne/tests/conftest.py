import sys
from unittest.mock import MagicMock, patch
import pytest

# Prepare mocks
mocks = {}

# LangChain Core
langchain_core = MagicMock()
langchain_core.documents = MagicMock()
class Document:
    def __init__(self, page_content, metadata=None):
        self.page_content = page_content
        self.metadata = metadata or {}
langchain_core.documents.Document = Document

mocks["langchain_core"] = langchain_core
mocks["langchain_core.documents"] = langchain_core.documents
mocks["langchain_core.embeddings"] = MagicMock()
mocks["langchain_core.vectorstores"] = MagicMock()
mocks["langchain_core.runnables"] = MagicMock()
mocks["langchain_core.output_parsers"] = MagicMock()
mocks["langchain_core.prompts"] = MagicMock()
mocks["langchain_core.language_models"] = MagicMock()

# LangChain Community
langchain_community = MagicMock()
langchain_community.vectorstores = MagicMock()
langchain_community.embeddings = MagicMock()
mocks["langchain_community"] = langchain_community
mocks["langchain_community.vectorstores"] = langchain_community.vectorstores
mocks["langchain_community.embeddings"] = langchain_community.embeddings

# PGVector
pgvector = MagicMock()
pgvector.sqlalchemy = MagicMock()
mocks["pgvector"] = pgvector
mocks["pgvector.sqlalchemy"] = pgvector.sqlalchemy

# Redis
redis_mock = MagicMock()
redis_mock.asyncio = MagicMock()
mocks["redis"] = redis_mock
mocks["redis.asyncio"] = redis_mock.asyncio

# Others
mocks["langchain_google_genai"] = MagicMock()
mocks["langchain_ollama"] = MagicMock()

# Start patcher
patcher = patch.dict(sys.modules, mocks)
patcher.start()

def pytest_sessionfinish(session, exitstatus):
    """Stop the patcher after the test session finishes."""
    patcher.stop()
