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
from sqlalchemy import text

async def find_relationship_path_bfs(self, source_entity: str, target_entity: str, max_depth: int = 3):
    await self.init_db()
    paths = []
    try:
        async with self.Session() as session:
            # Get entity IDs
            source_res = await session.execute(
                text("SELECT id FROM kg_entities WHERE name = :name"),
                {"name": source_entity}
            )
            source_row = source_res.fetchone()
            if not source_row: return []
            source_id = source_row[0]

            target_res = await session.execute(
                text("SELECT id FROM kg_entities WHERE name = :name"),
                {"name": target_entity}
            )
            target_row = target_res.fetchone()
            if not target_row: return []
            target_id = target_row[0]

            # BFS Queue: (current_id, current_path_nodes, current_path_rels)
            queue = [(source_id, [source_entity], [])]

            while queue:
                current_id, current_path, current_rels = queue.pop(0)
                depth = len(current_rels)

                if current_id == target_id and depth > 0:
                    paths.append({
                        "nodes": current_path,
                        "relations": current_rels,
                        "length": depth,
                        "confidence": 1.0 - (depth * 0.1)
                    })
                    if len(paths) >= 10: break
                    continue

                if depth >= max_depth:
                    continue

                # Get outgoing relations (N+1 issue!)
                stmt = text("""
                    SELECT r.target_id, r.relation, e.name
                    FROM kg_relations r
                    JOIN kg_entities e ON r.target_id = e.id
                    WHERE r.source_id = :source_id
                """)
                result = await session.execute(stmt, {"source_id": current_id})

                for row in result:
                    next_id = row[0]
                    relation = row[1]
                    next_name = row[2]

                    if next_name not in current_path:
                        queue.append(
                            (next_id, current_path + [next_name], current_rels + [relation])
                        )

        return paths
    except Exception as e:
        print(f"Path finding failed: {e}")
        return []

GraphManager.find_relationship_path_bfs = find_relationship_path_bfs

async def setup_data(mgr: GraphManager):
    await mgr.init_db()
    for i in range(10):
        await mgr.add_triple("A", f"rel1_{i}", f"B{i}")
        for j in range(10):
            await mgr.add_triple(f"B{i}", f"rel2_{j}", f"C{j}")
    for j in range(10):
        await mgr.add_triple(f"C{j}", "rel3", "D")

async def run_benchmark():
    mgr = GraphManager("sqlite+aiosqlite:///:memory:")
    await setup_data(mgr)

    start = time.perf_counter()
    paths = await mgr.find_relationship_path_bfs("A", "D", max_depth=3)
    end = time.perf_counter()

    duration = end - start
    print(f"BFS Path finding took {duration:.4f} seconds, found {len(paths)} paths.")

if __name__ == "__main__":
    asyncio.run(run_benchmark())
