
import sys
from unittest.mock import MagicMock

# Mock langchain dependencies to avoid installation
sys.modules["langchain_core"] = MagicMock()
sys.modules["langchain_core.documents"] = MagicMock()
sys.modules["langchain_core.embeddings"] = MagicMock()
sys.modules["langchain_core.vectorstores"] = MagicMock()
sys.modules["langchain_core.prompts"] = MagicMock()
sys.modules["langchain_core.runnables"] = MagicMock()
sys.modules["langchain_core.output_parsers"] = MagicMock()
sys.modules["langchain_core.language_models"] = MagicMock()

# Mock pgvector
sys.modules["pgvector"] = MagicMock()
sys.modules["pgvector.sqlalchemy"] = MagicMock()

# Mock redis
sys.modules["redis"] = MagicMock()
sys.modules["redis.asyncio"] = MagicMock()

# Mock SemanticManager for now as it uses langchain heavily
sys.modules["ippoc.mnemosyne.semantic.rag"] = MagicMock()
