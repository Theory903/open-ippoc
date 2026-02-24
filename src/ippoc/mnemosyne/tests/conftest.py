
import sys
from unittest.mock import MagicMock
import pytest
import types

def mock_module(module_name):
    """Helper to mock a module in sys.modules"""
    m = types.ModuleType(module_name)
    sys.modules[module_name] = m
    return m

# Mock heavy dependencies
lc_core = mock_module("langchain_core")
lc_core.documents = mock_module("langchain_core.documents")
lc_core.documents.Document = MagicMock()

lc_core.embeddings = mock_module("langchain_core.embeddings")
lc_core.embeddings.Embeddings = MagicMock()

lc_core.vectorstores = mock_module("langchain_core.vectorstores")
lc_core.vectorstores.VectorStore = MagicMock()

lc_core.prompts = mock_module("langchain_core.prompts")
lc_core.prompts.PromptTemplate = MagicMock()

lc_core.runnables = mock_module("langchain_core.runnables")
lc_core.runnables.Runnable = MagicMock()
lc_core.runnables.RunnablePassthrough = MagicMock()

lc_core.output_parsers = mock_module("langchain_core.output_parsers")
lc_core.output_parsers.StrOutputParser = MagicMock()

lc_core.language_models = mock_module("langchain_core.language_models")
lc_core.language_models.BaseLanguageModel = MagicMock()

lc_comm = mock_module("langchain_community")
lc_comm.vectorstores = mock_module("langchain_community.vectorstores")
lc_comm.vectorstores.pgvector = mock_module("langchain_community.vectorstores.pgvector")
lc_comm.vectorstores.pgvector.PGVector = MagicMock()

lc_comm.embeddings = mock_module("langchain_community.embeddings")

mock_module("pgvector")
pgv_sa = mock_module("pgvector.sqlalchemy")
pgv_sa.Vector = MagicMock()

mock_module("redis")
mock_module("redis.asyncio")
