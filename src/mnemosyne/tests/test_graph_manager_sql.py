import unittest
from mnemosyne.graph.manager import GraphManager
import math

class TestGraphManagerSQL(unittest.IsolatedAsyncioTestCase):
    async def test_find_similar_entities(self):
        # Setup in-memory DB
        db_url = "sqlite+aiosqlite:///:memory:"
        manager = GraphManager(db_url=db_url)
        await manager.init_db()

        # Create entities
        # A: overlaps with B (rel1->X), C (rel2->Y)
        # B: overlaps with A (rel1->X)
        # C: overlaps with A (rel2->Y)
        # D: no overlap

        # A has 3 relations
        await manager.add_triple("A", "rel1", "X")
        await manager.add_triple("A", "rel2", "Y")
        await manager.add_triple("A", "rel3", "Z")

        # B shares 1 with A. Total 1.
        await manager.add_triple("B", "rel1", "X")
        # Intersection(A,B) = 1 (rel1->X)
        # Union(A,B) = 3 + 1 - 1 = 3. Sim = 1/3 = 0.333...

        # C shares 1 with A. Total 2.
        await manager.add_triple("C", "rel2", "Y")
        await manager.add_triple("C", "rel4", "W")
        # Intersection(A,C) = 1 (rel2->Y)
        # Union(A,C) = 3 + 2 - 1 = 4. Sim = 1/4 = 0.25

        # D shares 0. Sim = 0.
        await manager.add_triple("D", "rel5", "V")

        # Test with threshold 0.0 (includes D in current impl)
        results_all = await manager.find_similar_entities("A", similarity_threshold=0.0)
        res_dict_all = {r["entity"]: r["similarity"] for r in results_all}

        self.assertIn("B", res_dict_all)
        self.assertIn("D", res_dict_all) # Expect D to be present currently
        self.assertEqual(res_dict_all["D"], 0.0)

        # Test with threshold 0.1 (excludes D)
        results = await manager.find_similar_entities("A", similarity_threshold=0.1)

        # Extract
        res_dict = {r["entity"]: r["similarity"] for r in results}

        self.assertIn("B", res_dict)
        self.assertAlmostEqual(res_dict["B"], 1/3, delta=0.001)
        self.assertIn("C", res_dict)
        self.assertAlmostEqual(res_dict["C"], 0.25, delta=0.001)
        self.assertNotIn("D", res_dict)
