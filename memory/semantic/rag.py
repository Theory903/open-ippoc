from typing import List, Optional, Dict
from langchain_core.documents import Document
from langchain_core.embeddings import Embeddings
from langchain_core.vectorstores import VectorStore
# Ideally use langchain_postgres if available, else standard interface
# We define the class to accept a generic VectorStore to be implementation agnostic

class SemanticManager:
    """
    Manages semantic memory retrieval and storage.
    Strictly uses LangChain Core interfaces.
    """
    def __init__(self, vector_store: VectorStore, embeddings: Embeddings):
        self.vector_store = vector_store
        self.embeddings = embeddings

    async def add_memory(self, text: str, metadata: Dict) -> List[str]:
        """
        Adds a single memory content to the vector store.
        Returns the list of IDs added.
        """
        doc = Document(page_content=text, metadata=metadata)
        # generic add_documents usually returns IDs
        return await self.vector_store.aadd_documents([doc])

    async def retrieve_relevant(self, query: str, k: int = 5) -> List[Document]:
        """
        Retrieves top-k relevant documents for a query.
        """
        # use as_retriever is the LCEL way, but direct search is also fine for a manager class
        # if this class is used within a chain, it should expose a generic runnable
        
        # Pure retrieval
        return await self.vector_store.asimilarity_search(query, k=k)

    def as_retriever(self, **kwargs):
        """
        Exposes the vector store as a standard LCEL retrieval runnable.
        """
        return self.vector_store.as_retriever(**kwargs)
