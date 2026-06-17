import sys
from unittest.mock import MagicMock
import types

# Mock missing dependencies globally for pytest
def mock_package(name):
    m = types.ModuleType(name)
    m.__path__ = []
    sys.modules[name] = m
    return m

mock_package("langchain_core")
sys.modules["langchain_core.documents"] = MagicMock()
sys.modules["langchain_core.embeddings"] = MagicMock()
sys.modules["langchain_core.vectorstores"] = MagicMock()
sys.modules["langchain_core.prompts"] = MagicMock()
sys.modules["langchain_core.runnables"] = MagicMock()
sys.modules["langchain_core.output_parsers"] = MagicMock()
sys.modules["langchain_core.language_models"] = MagicMock()

mock_package("langchain_community")
sys.modules["langchain_community.vectorstores"] = MagicMock()

mock_package("langchain_google_genai")

sys.modules["pgvector"] = MagicMock()
sys.modules["pgvector.sqlalchemy"] = MagicMock()
sys.modules["redis"] = MagicMock()
sys.modules["redis.asyncio"] = MagicMock()
