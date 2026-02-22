import sys
from unittest.mock import MagicMock
import types
import pytest
from sqlalchemy.types import TypeEngine

# Mock heavy dependencies that are not needed for graph tests
# This must happen before any imports from ippoc.mnemosyne
def pytest_configure(config):
    modules_to_mock = [
        "langchain_core",
        "langchain_core.documents",
        "langchain_core.embeddings",
        "langchain_core.vectorstores",
        "langchain_core.prompts",
        "langchain_core.runnables",
        "langchain_core.output_parsers",
        "langchain_core.language_models",
        "langchain_community",
        "langchain_community.vectorstores",
        "langchain_google_genai",
        "langchain_postgres",
        "langgraph",
        "psycopg2",
        "pgvector",
        "pgvector.sqlalchemy",
        "redis",
        "redis.asyncio",
    ]

    for module_name in modules_to_mock:
        # We must make sure parent packages exist too
        parts = module_name.split('.')
        for i in range(1, len(parts) + 1):
            parent_name = '.'.join(parts[:i])
            if parent_name not in sys.modules:
                sys.modules[parent_name] = types.ModuleType(parent_name)

    # Specifically for Document, we need a class if it's instantiated
    class Document:
        def __init__(self, page_content, metadata=None):
            self.page_content = page_content
            self.metadata = metadata or {}

    sys.modules["langchain_core.documents"].Document = Document

    # Mock other classes imported directly
    sys.modules["langchain_core.embeddings"].Embeddings = MagicMock
    sys.modules["langchain_core.vectorstores"].VectorStore = MagicMock
    sys.modules["langchain_core.prompts"].PromptTemplate = MagicMock
    sys.modules["langchain_core.runnables"].Runnable = MagicMock
    sys.modules["langchain_core.output_parsers"].StrOutputParser = MagicMock

    # Mock pgvector Vector type
    class Vector(TypeEngine):
        def __init__(self, dim):
            super().__init__()
            self.dim = dim

    sys.modules["pgvector.sqlalchemy"].Vector = Vector
