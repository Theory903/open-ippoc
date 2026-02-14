import sys
import os
import asyncio
import time
from sqlalchemy import text

# Ensure src is in path
sys.path.append(os.path.join(os.getcwd(), "src"))

from ippoc.mnemosyne.graph.manager import GraphManager

class SimulatedBFSGraphManager(GraphManager):
    """
    Simulates the unoptimized N+1 BFS path finding.
    """
    async def find_relationship_path(self, source_entity: str, target_entity: str, max_depth: int = 3):
        await self.init_db()
        paths = []

        async with self.Session() as session:
            # Get entity IDs
            source_res = await session.execute(
                text("SELECT id FROM kg_entities WHERE name = :name"),
                {"name": source_entity}
            )
            source_row = source_res.fetchone()
            if not source_row:
                return []
            source_id = source_row[0]

            target_res = await session.execute(
                text("SELECT id FROM kg_entities WHERE name = :name"),
                {"name": target_entity}
            )
            target_row = target_res.fetchone()
            if not target_row:
                return []
            target_id = target_row[0]

            # Naive BFS
            # queue items: (current_id, path_ids, path_rels, path_names)
            # source_id is NOT in the path_ids list in the CTE implementation result (it returns nodes [A, B, C] for A->B->C?)
            # Let's check CTE implementation:
            # nodes = [] ... for nid in ids: name = id_to_name.get(nid)
            # The CTE base case: SELECT target_id, source_id || ',' || target_id ...
            # So the path includes source and target.

            # Initial state: We are at source_id. Path so far is [source_id].
            # But the BFS queue explores *neighbors*.

            # Let's match CTE output format loosely.
            queue = [(source_id, [source_id], [], [source_entity])]

            while queue:
                current_id, path_ids, path_rels, path_names = queue.pop(0)

                if len(path_ids) - 1 >= max_depth: # depth is number of edges
                    continue

                # N+1 Query here: Get outgoing relations for EACH node visited
                stmt = text("""
                    SELECT r.target_id, r.relation, e.name
                    FROM kg_relations r
                    JOIN kg_entities e ON r.target_id = e.id
                    WHERE r.source_id = :source_id
                """)
                result = await session.execute(stmt, {"source_id": current_id})
                neighbors = result.fetchall()

                for row in neighbors:
                    neighbor_id = row[0]
                    relation = row[1]
                    neighbor_name = row[2]

                    new_path_ids = path_ids + [neighbor_id]
                    new_path_rels = path_rels + [relation]
                    new_path_names = path_names + [neighbor_name]

                    if neighbor_id == target_id:
                        # Found path
                        paths.append({
                            "nodes": new_path_names,
                            "relations": new_path_rels,
                            "length": len(new_path_rels),
                            "confidence": 1.0
                        })
                        if len(paths) >= 10:
                            return paths
                    else:
                        queue.append((neighbor_id, new_path_ids, new_path_rels, new_path_names))

        return paths

async def run_benchmark():
    # Use file DB so both managers can access it
    db_path = "benchmark_graph.db"
    if os.path.exists(db_path):
        os.remove(db_path)

    db_url = f"sqlite+aiosqlite:///{db_path}"

    print("Initializing DB...")
    gm = GraphManager(db_url=db_url)
    await gm.init_db()

    print("Populating graph (this may take a moment)...")
    # Create a layered graph
    # Layers: 4, Width: 8
    # Connectivity: Dense between layers
    layers = 4
    width = 8

    # Start -> Layer 0
    await gm.add_triple("START", "entry", "L0_0")

    for i in range(layers):
        for j in range(width):
            src = f"L{i}_{j}"
            # Connect to next layer
            if i < layers - 1:
                # Connect to multiple nodes in next layer to create branching
                for k in range(width):
                    # Connect to all nodes in next layer (Dense)
                    tgt = f"L{i+1}_{k}"
                    await gm.add_triple(src, "next", tgt)

    # Layer N-1 -> END
    await gm.add_triple(f"L{layers-1}_{width-1}", "exit", "END")

    print("Graph populated.")

    # 1. Benchmark CTE (Optimized)
    print("\n--- Benchmarking CTE (Optimized) ---")
    start_cte = time.time()
    res_cte = await gm.find_relationship_path("START", "END", max_depth=6)
    cte_time = time.time() - start_cte
    print(f"CTE Time: {cte_time:.4f}s")
    print(f"Paths found: {len(res_cte)}")

    # 2. Benchmark BFS (Unoptimized)
    print("\n--- Benchmarking BFS (Unoptimized) ---")
    bfs_gm = SimulatedBFSGraphManager(db_url=db_url)
    start_bfs = time.time()
    res_bfs = await bfs_gm.find_relationship_path("START", "END", max_depth=6)
    bfs_time = time.time() - start_bfs
    print(f"BFS Time: {bfs_time:.4f}s")
    print(f"Paths found: {len(res_bfs)}")

    # Cleanup
    if os.path.exists(db_path):
        os.remove(db_path)

    # Results
    print("\n--- Results ---")
    if cte_time < bfs_time:
        speedup = bfs_time / cte_time
        print(f"✅ VERIFIED: CTE is {speedup:.2f}x faster than BFS.")
    else:
        print(f"❌ FAILED: CTE ({cte_time:.4f}s) is slower than BFS ({bfs_time:.4f}s).")

if __name__ == "__main__":
    asyncio.run(run_benchmark())
