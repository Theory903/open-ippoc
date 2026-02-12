import asyncio
import unittest
import sys
import os
from typing import List, Optional, Any, Iterable
from datetime import datetime
from uuid import uuid4

# Add src/ippoc to path
sys.path.append(os.path.join(os.getcwd(), 'src/ippoc'))
# And src to allow importing ippoc.mnemosyne
sys.path.append(os.path.join(os.getcwd(), 'src'))

from langchain_core.vectorstores import VectorStore
from langchain_core.documents import Document
from langchain_core.embeddings import Embeddings

from mnemosyne.core import MemorySystem

class SimpleVectorStore(VectorStore):
    def __init__(self):
        self.docs = {}  # id -> Document

    def add_texts(self, texts: Iterable[str], metadatas: Optional[List[dict]] = None, **kwargs: Any) -> List[str]:
        ids = []
        for i, text in enumerate(texts):
            doc_id = str(uuid4())
            metadata = metadatas[i] if metadatas else {}
            self.docs[doc_id] = Document(page_content=text, metadata=metadata)
            ids.append(doc_id)
        return ids

    async def aadd_documents(self, documents: List[Document], **kwargs: Any) -> List[str]:
        ids = []
        for doc in documents:
            if doc.id:
                doc_id = doc.id
            else:
                doc_id = str(uuid4())
            self.docs[doc_id] = doc
            ids.append(doc_id)
        return ids

    def similarity_search(self, query: str, k: int = 4, **kwargs: Any) -> List[Document]:
        # Simple implementation: return all docs containing query words
        results = []
        for doc in self.docs.values():
            if query.lower() in doc.page_content.lower():
                results.append(doc)
        return results[:k]

    async def asimilarity_search_with_score(self, query: str, k: int = 4, filter: Optional[dict] = None, **kwargs: Any) -> List[tuple[Document, float]]:
        # Mock implementation
        results = []
        for doc in self.docs.values():
            # Apply filter
            if filter:
                match = True
                for key, val in filter.items():
                    if doc.metadata.get(key) != val:
                        match = False
                        break
                if not match:
                    continue

            if query.lower() in doc.page_content.lower():
                results.append((doc, 0.9))
        return results[:k]

    async def adelete(self, ids: Optional[List[str]] = None, **kwargs: Any) -> Optional[bool]:
        deleted = False
        if ids:
            for i in ids:
                if i in self.docs:
                    del self.docs[i]
                    deleted = True
        return deleted

    @classmethod
    def from_texts(cls, texts: List[str], embedding: Embeddings, metadatas: Optional[List[dict]] = None, **kwargs: Any):
        store = cls()
        store.add_texts(texts, metadatas)
        return store

class SimpleEmbeddings(Embeddings):
    def embed_documents(self, texts: List[str]) -> List[List[float]]:
        return [[0.1] * 10 for _ in texts]

    def embed_query(self, text: str) -> List[float]:
        return [0.1] * 10

    async def aembed_documents(self, texts: List[str]) -> List[List[float]]:
        return [[0.1] * 10 for _ in texts]

    async def aembed_query(self, text: str) -> List[float]:
        return [0.1] * 10

class TestForgetIntegration(unittest.IsolatedAsyncioTestCase):
    async def asyncSetUp(self):
        self.db_url = "sqlite+aiosqlite:///:memory:"
        self.vector_store = SimpleVectorStore()
        self.embeddings = SimpleEmbeddings()

        self.memory = MemorySystem(
            db_url=self.db_url,
            vector_store=self.vector_store,
            embeddings=self.embeddings
        )
        await self.memory.initialize()

    async def test_forget_flow(self):
        # 1. Populate Memory

        # Episodic
        ep_id1 = await self.memory.store_episodic("User greeted", source="user", metadata={"type": "greeting"})
        ep_id2 = await self.memory.store_episodic("System replied", source="system", metadata={"type": "reply"})
        # Extract numeric ID
        ep_id1_num = int(ep_id1.split(":")[1])
        ep_id2_num = int(ep_id2.split(":")[1])

        # Semantic
        # store_semantic returns object_ids (from SemanticManager)
        sem_ids = await self.memory.store_semantic("Python is a programming language", metadata={"topic": "coding"})
        sem_id1 = sem_ids[0]

        # Procedural
        await self.memory.register_skill("hello_world", "print('Hello')", "Prints hello", "python")

        # Graph
        await self.memory.add_relation("Python", "is_a", "Language")
        await self.memory.add_relation("Java", "is_a", "Language")

        # Verify initial state
        # Episodic search
        events = await self.memory.episodic.search("greeted")
        self.assertEqual(len(events), 1)

        # Semantic search
        docs = await self.memory.semantic.retrieve_relevant("Python")
        self.assertTrue(len(docs) >= 1)

        # Procedural search
        skill = await self.memory.procedural.get_skill("hello_world")
        self.assertIsNotNone(skill)

        # Graph search
        neighbors = await self.memory.graph.get_neighbors("Python")
        self.assertTrue(len(neighbors) > 0)

        # 2. Forget Operation
        criteria = {
            "episodic": {"ids": [ep_id1_num]}, # Forget greeting
            "semantic": {"ids": [sem_id1]},   # Forget Python fact
            "procedural": {"skills": ["hello_world"]}, # Forget skill
            "graph": {"entities": ["Python"]} # Forget Python entity
        }

        count = await self.memory.forget(criteria)

        # 3. Verification

        # Episodic: greeting should be gone, reply should remain
        events_greet = await self.memory.episodic.search("greeted")
        self.assertEqual(len(events_greet), 0, "Episodic memory should be deleted")

        events_reply = await self.memory.episodic.search("replied")
        self.assertEqual(len(events_reply), 1, "Other episodic memory should remain")

        # Semantic: Python fact should be gone
        # The vector store mocks deletion by ID.
        # If SemanticManager passed object_id, and vector_store used generated ID, then deletion failed.
        # We check if the document is still in the store.
        # Since we only added one doc (chunked maybe?), let's check store size or content.

        # Search again
        docs_after = await self.memory.semantic.retrieve_relevant("Python")
        # If deleted, this should return empty or at least not the deleted one
        # But retrieve_relevant uses similarity search, which uses vector_store.docs
        # So if deletion failed, this will return the doc.
        self.assertEqual(len(docs_after), 0, "Semantic memory should be deleted")

        # Procedural: skill should be gone
        skill_after = await self.memory.procedural.get_skill("hello_world")
        self.assertIsNone(skill_after, "Skill should be deleted")

        # Graph: Python entity should be gone
        neighbors_after = await self.memory.graph.get_neighbors("Python")
        self.assertEqual(len(neighbors_after), 0, "Graph entity should be deleted")

        # Check that Java is still there
        neighbors_java = await self.memory.graph.get_neighbors("Java")
        self.assertTrue(len(neighbors_java) > 0, "Other graph entity should remain")

        print(f"Total forgotten items: {count}")

if __name__ == "__main__":
    unittest.main()
