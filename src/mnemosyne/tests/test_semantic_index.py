
import unittest
import asyncio
from unittest.mock import MagicMock
import sys
from pathlib import Path

# Add src to path
sys.path.insert(0, str(Path.cwd() / "src"))

from mnemosyne.semantic.rag import SemanticManager, SemanticObject, ContentType

class TestSemanticIndex(unittest.TestCase):
    def setUp(self):
        self.vector_store = MagicMock()
        # Make mocks awaitable
        f1 = asyncio.Future()
        f1.set_result(["doc_1"])
        self.vector_store.aadd_documents = MagicMock(return_value=f1)

        f2 = asyncio.Future()
        f2.set_result([])
        self.vector_store.asimilarity_search_with_score = MagicMock(return_value=f2)

        self.embeddings = MagicMock()
        f3 = asyncio.Future()
        f3.set_result([])
        self.embeddings.aembed_documents = MagicMock(return_value=f3)

        self.manager = SemanticManager(self.vector_store, self.embeddings)

    def test_index_population(self):
        """Test that the component index is correctly populated and used for retrieval."""
        async def run_test():
            # Add a memory with capitalized words so they are extracted as components
            await self.manager.add_memory(
                "Project Alpha is a top secret initiative.",
                {"type": "project"},
                ContentType.TEXT
            )

            # Check if index is populated
            # Components should include "Project Alpha"
            # Note: The regex finds "Project Alpha" as one term if they are adjacent capitalized words.
            # Let's verify what components are extracted.

            # Access the object
            self.assertEqual(len(self.manager.semantic_objects), 1)
            obj = self.manager.semantic_objects[0]
            components = obj.semantic_components
            print(f"Extracted components: {components}")

            # Verify index
            for comp in components:
                self.assertIn(comp, self.manager.component_index)
                self.assertIn(obj, self.manager.component_index[comp])

            # Now retrieval
            # Query with a matching component
            results = await self.manager.retrieve_relevant("Project Alpha", k=5, min_score=0.1)
            self.assertEqual(len(results), 1)
            self.assertEqual(results[0].metadata["object_id"], obj.id)

            # Query with non-matching component
            results_none = await self.manager.retrieve_relevant("Project Beta", k=5, min_score=0.1)
            # "Project Beta" -> components ["Project Beta"] (if valid)
            # "Project Alpha" has "Project Alpha". Overlap 0?
            # Or "Project" and "Alpha"?
            # Regex: [A-Z][a-z]+(?:\s+[A-Z][a-z]+)*
            # "Project Alpha" is one token.
            # "Project Beta" is one token.
            # No overlap.
            self.assertEqual(len(results_none), 0)

            # Verify no memory leak (querying missing term shouldn't add it to index)
            missing_term = "NonExistentTerm"
            await self.manager.retrieve_relevant(missing_term, k=5, min_score=0.1)
            self.assertNotIn(missing_term, self.manager.component_index)

        asyncio.run(run_test())

if __name__ == '__main__':
    unittest.main()
