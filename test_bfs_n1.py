import asyncio
import time
import sys
import os

sys.path.insert(0, os.path.abspath('src/ippoc'))

import importlib.util
spec = importlib.util.spec_from_file_location("manager", "src/ippoc/mnemosyne/graph/manager.py")
manager_module = importlib.util.module_from_spec(spec)
sys.modules["mnemosyne.graph.manager"] = manager_module
spec.loader.exec_module(manager_module)

GraphManager = manager_module.GraphManager
from sqlalchemy import text, bindparam

async def find_relationship_path_optimized(self, source_entity: str, target_entity: str, max_depth: int = 3):
    await self.init_db()
    paths = []
    try:
        async with self.Session() as session:
            # Get entity IDs (Bulk fetch)
            stmt = text("SELECT id, name FROM kg_entities WHERE name IN (:source, :target)")
            res = await session.execute(stmt, {"source": source_entity, "target": target_entity})

            source_id = None
            target_id = None

            for row in res:
                if row.name == source_entity:
                    source_id = row.id
                if row.name == target_entity:
                    target_id = row.id

            if source_id is None or target_id is None:
                return []

            # BFS Queue: (current_id, current_path_nodes, current_path_rels)
            queue = [(source_id, [source_entity], [])]

            while queue:
                # Process current level in bulk
                level_nodes = []
                for item in queue:
                    level_nodes.append(item[0])

                if not level_nodes:
                    break

                # We could bulk fetch, but wait, the prompt asks to optimize:
                # Get outgoing relations (N+1 query in BFS Path Finding)
                # The code shown in the task description matches the BFS approach, but in the actual file, the CTE approach is used!

                # Wait, does the actual codebase use CTE or BFS?
                # Ah! The task description shows:
                '''
                if depth >= max_depth:
                    continue

                # Get outgoing relations
                stmt = text("""
                    SELECT r.target_id, r.relation, e.name
                    FROM kg_relations r
                    JOIN kg_entities e ON r.target_id = e.id
                    WHERE r.source_id = :source_id
                """)
                result = await session.execute(stmt, {"source_id": current_id})
                '''

                # Let's check `manager.py` again. Oh, it DOES have CTE.
                pass

        return paths
    except Exception as e:
        print(f"Path finding failed: {e}")
        return []
