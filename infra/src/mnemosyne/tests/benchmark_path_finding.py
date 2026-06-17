import asyncio
import sys
import os
import time
import random
from pathlib import Path
from sqlalchemy import text, bindparam

# Add infra/src to python path to allow imports
sys.path.insert(0, str(Path(__file__).parent.parent.parent))

try:
    from mnemosyne.graph.manager import GraphManager
except ImportError:
    # Attempt to add current dir to path if running directly
    sys.path.append(os.getcwd())
    from infra.src.mnemosyne.graph.manager import GraphManager

async def find_relationship_path_bfs(session, source_id, target_id, max_depth):
    """
    Unoptimized BFS implementation with N+1 query.
    Simulates the code that was replaced by CTE.
    """
    # Queue stores (current_id, path_ids, path_rels)
    # path_ids includes the start node
    queue = [(source_id, [source_id], [])]
    results = []

    # We limit iterations to avoid infinite loops in cyclic graphs if logic is flawed,
    # but the loop condition and depth check should handle it.
    steps = 0
    max_steps = 10000

    while queue and steps < max_steps:
        steps += 1
        current_id, path_ids, path_rels = queue.pop(0)

        depth = len(path_rels)
        if depth >= max_depth:
            continue

        # THE N+1 QUERY (The performance bottleneck)
        stmt = text("""
            SELECT r.target_id, r.relation, e.name
            FROM kg_relations r
            JOIN kg_entities e ON r.target_id = e.id
            WHERE r.source_id = :source_id
        """)
        res = await session.execute(stmt, {"source_id": current_id})
        rows = res.fetchall()

        for row in rows:
            next_id = row[0]
            relation = row[1]
            # name = row[2] # We fetch name but might not use it immediately in path logic

            if next_id == target_id:
                # Found a path
                new_path_ids = path_ids + [next_id]
                new_path_rels = path_rels + [relation]
                results.append({
                    "ids": new_path_ids,
                    "rels": new_path_rels
                })
                if len(results) >= 10: # Match CTE limit
                    return results
            elif next_id not in path_ids: # Avoid cycles
                new_path_ids = path_ids + [next_id]
                new_path_rels = path_rels + [relation]
                queue.append((next_id, new_path_ids, new_path_rels))

    return results

async def run_benchmark():
    # Use in-memory SQLite for speed and isolation
    db_url = "sqlite+aiosqlite:///:memory:"
    gm = GraphManager(db_url=db_url)
    await gm.init_db()

    print("Populating database with a dense graph...")

    # Create a graph with:
    # - Depth 5
    # - Branching factor 5
    # - Total nodes ~ 5^5 = 3125 (approx)

    async with gm.Session() as session:
        # Create Root "Start"
        await session.execute(text("INSERT INTO kg_entities (name, type) VALUES ('Start', 'Concept')"))
        res = await session.execute(text("SELECT id FROM kg_entities WHERE name='Start'"))
        start_id = res.scalar()

        # Create Target "End"
        await session.execute(text("INSERT INTO kg_entities (name, type) VALUES ('End', 'Concept')"))
        res = await session.execute(text("SELECT id FROM kg_entities WHERE name='End'"))
        end_id = res.scalar()

        current_layer = [start_id]
        all_ids = [start_id, end_id]

        # Build layers
        for layer in range(4):
            next_layer = []
            print(f"Building layer {layer+1}...")

            # Create nodes for next layer
            layer_nodes_count = len(current_layer) * 5
            # Bulk insert entities
            names = [f"L{layer+1}_{i}" for i in range(layer_nodes_count)]

            # Chunking because SQLite has variable limit
            chunk_size = 100
            new_ids = []

            for i in range(0, len(names), chunk_size):
                chunk = names[i:i+chunk_size]
                values = ", ".join([f"('{n}', 'Node')" for n in chunk])
                await session.execute(text(f"INSERT INTO kg_entities (name, type) VALUES {values}"))

            # Get IDs back
            # In SQLite, reliable way is by name patterns since we just inserted them
            res = await session.execute(text(f"SELECT id FROM kg_entities WHERE name LIKE 'L{layer+1}_%'"))
            new_ids = [r[0] for r in res.fetchall()]
            all_ids.extend(new_ids)

            # Link current layer to next layer
            # Each node in current_layer connects to 5 random nodes in next_layer
            # To guarantee paths, ensure connectivity

            rel_values = []

            # Distribute connections
            # Simple: node i in current connects to nodes i*5 ... i*5+5 in next
            # This creates a tree-like expansion
            for i, source_id in enumerate(current_layer):
                children_indices = range(i*5, min((i+1)*5, len(new_ids)))
                for idx in children_indices:
                    target_id = new_ids[idx]
                    rel_values.append(f"({source_id}, {target_id}, 'connects_to')")

            # Bulk insert relations
            if rel_values:
                # Chunking
                for i in range(0, len(rel_values), chunk_size):
                    chunk = rel_values[i:i+chunk_size]
                    v = ", ".join(chunk)
                    await session.execute(text(f"INSERT INTO kg_relations (source_id, target_id, relation) VALUES {v}"))

            current_layer = new_ids

        # Connect last layer to End
        print("Connecting to End node...")
        rel_values = []
        for source_id in current_layer:
            rel_values.append(f"({source_id}, {end_id}, 'finishes_at')")

        for i in range(0, len(rel_values), chunk_size):
            chunk = rel_values[i:i+chunk_size]
            v = ", ".join(chunk)
            await session.execute(text(f"INSERT INTO kg_relations (source_id, target_id, relation) VALUES {v}"))

        await session.commit()

    print(f"Graph populated. Total nodes: {len(all_ids)}")

    print("\n--- Benchmarking Path Finding ---")
    print("Searching for paths from 'Start' to 'End' (depth 5)")

    # 1. Benchmark Optimized (CTE)
    start_time = time.time()
    iterations = 50
    found_count = 0

    for _ in range(iterations):
        paths = await gm.find_relationship_path("Start", "End", max_depth=6)
        if paths:
            found_count += 1

    end_time = time.time()
    cte_time = (end_time - start_time) / iterations
    print(f"CTE (Optimized) Average Time: {cte_time:.5f}s")
    print(f"CTE Found paths: {found_count > 0}")

    # 2. Benchmark Unoptimized (BFS)
    # We need to manually invoke it using session
    async with gm.Session() as session:
        start_time = time.time()
        found_count_bfs = 0

        for _ in range(iterations):
            # Resolve IDs first as inputs
            s_res = await session.execute(text("SELECT id FROM kg_entities WHERE name='Start'"))
            s_id = s_res.scalar()
            e_res = await session.execute(text("SELECT id FROM kg_entities WHERE name='End'"))
            e_id = e_res.scalar()

            paths = await find_relationship_path_bfs(session, s_id, e_id, max_depth=6)
            if paths:
                found_count_bfs += 1

        end_time = time.time()
        bfs_time = (end_time - start_time) / iterations
        print(f"BFS (Unoptimized) Average Time: {bfs_time:.5f}s")
        print(f"BFS Found paths: {found_count_bfs > 0}")

    print("\n--- Results ---")
    if bfs_time > 0:
        improvement = bfs_time / cte_time
        print(f"Speedup: {improvement:.2f}x")
    else:
        print("BFS time was 0, cannot calculate speedup.")

if __name__ == "__main__":
    asyncio.run(run_benchmark())
