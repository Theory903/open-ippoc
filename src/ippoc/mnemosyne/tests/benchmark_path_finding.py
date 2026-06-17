
import asyncio
import time
import random
import logging
import sys
import os
import importlib.util
from typing import List, Dict, Any, Tuple
from sqlalchemy import text, bindparam
from sqlalchemy.ext.asyncio import AsyncSession

# Set up logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Import GraphManager directly from file to avoid package dependencies
file_path = os.path.join(os.getcwd(), "src/ippoc/mnemosyne/graph/manager.py")
spec = importlib.util.spec_from_file_location("manager", file_path)
manager_module = importlib.util.module_from_spec(spec)
sys.modules["manager"] = manager_module
spec.loader.exec_module(manager_module)

GraphManager = manager_module.GraphManager
Base = manager_module.Base

async def find_path_bfs_unoptimized(session: AsyncSession, source_id: int, target_id: int, max_depth: int):
    """
    Simulates the unoptimized N+1 BFS path finding.
    """
    queue = [(source_id, [source_id], [])] # (current_id, path_ids, path_rels)
    paths = []

    # We need a visited set per path to avoid cycles in that path,
    # but for BFS we usually want shortest paths.
    # The snippet implies a simple traversal.

    while queue:
        current_id, path_ids, path_rels = queue.pop(0)

        if len(path_ids) > max_depth + 1:
            continue

        if current_id == target_id:
            if len(path_ids) > 1:
                paths.append({
                    "ids": path_ids,
                    "rels": path_rels,
                    "length": len(path_rels)
                })
            continue

        # N+1 Query here
        stmt = text("""
            SELECT r.target_id, r.relation
            FROM kg_relations r
            WHERE r.source_id = :source_id
        """)
        result = await session.execute(stmt, {"source_id": current_id})

        for row in result.fetchall():
            next_id = row[0]
            relation = row[1]

            if next_id not in path_ids: # Avoid simple cycles
                new_path_ids = path_ids + [next_id]
                new_path_rels = path_rels + [relation]
                queue.append((next_id, new_path_ids, new_path_rels))

    return paths

async def find_path_cte_optimized_cycle_check(session: AsyncSession, source_id: int, target_id: int, max_depth: int):
    """
    Optimized CTE with in-SQL cycle detection.
    """
    # SQLite instr version
    # checks if ',' || target_id || ',' is in ',' || path_ids || ','
    cte_query = text("""
        WITH RECURSIVE path_search(last_id, path_ids, path_rels, depth) AS (
            -- Base case
            SELECT
                target_id,
                cast(source_id as text) || ',' || cast(target_id as text),
                cast(relation as text),
                1
            FROM kg_relations
            WHERE source_id = :source_id

            UNION ALL

            -- Recursive step
            SELECT
                r.target_id,
                p.path_ids || ',' || cast(r.target_id as text),
                p.path_rels || ',' || cast(r.relation as text),
                p.depth + 1
            FROM kg_relations r
            JOIN path_search p ON r.source_id = p.last_id
            WHERE p.depth < :max_depth
            AND instr(',' || p.path_ids || ',', ',' || cast(r.target_id as text) || ',') = 0
        )
        SELECT path_ids, path_rels, depth
        FROM path_search
        WHERE last_id = :target_id
        ORDER BY depth ASC
        LIMIT 10
    """)

    result = await session.execute(cte_query, {
        "source_id": source_id,
        "target_id": target_id,
        "max_depth": max_depth
    })
    return result.fetchall()

async def setup_graph(gm: GraphManager, num_nodes=100, num_edges=500):
    await gm.init_db()

    # Create nodes
    for i in range(num_nodes):
        await gm.add_triple(f"Node_{i}", "connected_to", f"Node_{i+1 if i < num_nodes-1 else 0}")

    # Add random edges to create complexity/cycles
    for _ in range(num_edges):
        u = random.randint(0, num_nodes-1)
        v = random.randint(0, num_nodes-1)
        if u != v:
            await gm.add_triple(f"Node_{u}", "random_link", f"Node_{v}")

async def run_benchmark():
    db_url = "sqlite+aiosqlite:///:memory:"
    gm = GraphManager(db_url=db_url)

    print("Setting up graph...")
    await setup_graph(gm, num_nodes=200, num_edges=800)

    source = "Node_0"
    target = "Node_10"
    max_depth = 4

    print(f"Benchmarking path finding from {source} to {target} (depth={max_depth})...")

    async with gm.Session() as session:
        # Get IDs
        res = await session.execute(text("SELECT id FROM kg_entities WHERE name = :n"), {"n": source})
        source_id = res.scalar()
        res = await session.execute(text("SELECT id FROM kg_entities WHERE name = :n"), {"n": target})
        target_id = res.scalar()

        if not source_id or not target_id:
            print("Source or target not found")
            return

        # 1. Baseline: Unoptimized BFS
        start_time = time.time()
        for _ in range(5):
             await find_path_bfs_unoptimized(session, source_id, target_id, max_depth)
        bfs_time = (time.time() - start_time) / 5
        print(f"Unoptimized BFS (avg): {bfs_time:.4f}s")

        # 2. Current CTE
        start_time = time.time()
        for _ in range(5):
            await gm._find_paths_cte(session, source_id, target_id, max_depth)
        cte_current_time = (time.time() - start_time) / 5
        print(f"Current CTE (avg): {cte_current_time:.4f}s")

        # 3. Optimized CTE with Cycle Check (instr)
        start_time = time.time()
        for _ in range(5):
            await find_path_cte_optimized_cycle_check(session, source_id, target_id, max_depth)
        cte_opt_time = (time.time() - start_time) / 5
        print(f"Optimized CTE (avg): {cte_opt_time:.4f}s")

        # 4. Optimized CTE with Cycle Check (NOT LIKE) - Portable
        async def find_path_cte_portable(session, source_id, target_id, max_depth):
            cte_query = text("""
                WITH RECURSIVE path_search(last_id, path_ids, path_rels, depth) AS (
                    -- Base case
                    SELECT
                        target_id,
                        cast(source_id as text) || ',' || cast(target_id as text),
                        cast(relation as text),
                        1
                    FROM kg_relations
                    WHERE source_id = :source_id

                    UNION ALL

                    -- Recursive step
                    SELECT
                        r.target_id,
                        p.path_ids || ',' || cast(r.target_id as text),
                        p.path_rels || ',' || cast(r.relation as text),
                        p.depth + 1
                    FROM kg_relations r
                    JOIN path_search p ON r.source_id = p.last_id
                    WHERE p.depth < :max_depth
                    AND (',' || p.path_ids || ',') NOT LIKE ('%,' || cast(r.target_id as text) || ',%')
                )
                SELECT path_ids, path_rels, depth
                FROM path_search
                WHERE last_id = :target_id
                ORDER BY depth ASC
                LIMIT 10
            """)
            result = await session.execute(cte_query, {
                "source_id": source_id,
                "target_id": target_id,
                "max_depth": max_depth
            })
            return result.fetchall()

        start_time = time.time()
        for _ in range(5):
            await find_path_cte_portable(session, source_id, target_id, max_depth)
        cte_portable_time = (time.time() - start_time) / 5
        print(f"Portable Optimized CTE (avg): {cte_portable_time:.4f}s")

        improvement_vs_bfs = bfs_time / cte_current_time if cte_current_time > 0 else 0
        improvement_opt_vs_current = cte_current_time / cte_opt_time if cte_opt_time > 0 else 0
        improvement_portable_vs_current = cte_current_time / cte_portable_time if cte_portable_time > 0 else 0

        print(f"Speedup CTE vs BFS: {improvement_vs_bfs:.2f}x")
        print(f"Speedup Opt CTE vs Current CTE: {improvement_opt_vs_current:.2f}x")
        print(f"Speedup Portable CTE vs Current CTE: {improvement_portable_vs_current:.2f}x")

if __name__ == "__main__":
    asyncio.run(run_benchmark())
