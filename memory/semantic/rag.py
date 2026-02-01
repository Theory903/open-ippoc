import os
from typing import List, Dict, Any
from langchain_community.vectorstores import PGVector
from langchain_openai import OpenAIEmbeddings
from langchain.schema import Document
from pydantic import BaseModel

class SemanticConfig(BaseModel):
    connection_string: str = os.getenv("DATABASE_URL", "postgresql://user:pass@localhost:5432/ippoc")
    collection_name: str = "hippocampus_v1"
    embedding_model: str = "text-embedding-3-small"

class SemanticManager:
    def __init__(self, config: SemanticConfig = SemanticConfig()):
        self.config = config
        self.embeddings = OpenAIEmbeddings(model=config.embedding_model)
        
        # Initialize PGVector (requires pgvector extension in DB)
        self.vector_store = PGVector(
            connection_string=self.config.connection_string,
            embedding_function=self.embeddings,
            collection_name=self.config.collection_name,
            use_jsonb=True,
        )

    async def search(self, query: str, limit: int = 5, min_score: float = 0.7) -> List[Dict[str, Any]]:
        """
        Semantic search using HNSW index
        """
        docs_with_scores = await self.vector_store.asimilarity_search_with_relevance_scores(
            query, k=limit
        )
        
        results = []
        for doc, score in docs_with_scores:
            if score >= min_score:
                results.append({
                    "content": doc.page_content,
                    "score": score,
                    "metadata": doc.metadata,
                    "type": "semantic"
                })
        return results

    async def index(self, content: str, metadata: Dict[str, Any]):
        """
        Embed and store knowledge
        """
        doc = Document(page_content=content, metadata=metadata)
        await self.vector_store.aadd_documents([doc])
