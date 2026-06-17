import asyncio
import sys
import os
import time
from typing import List, Dict, Any
from sqlalchemy import text
from unittest.mock import MagicMock, patch
import types

# Inject path to find the module if needed
sys.path.append(os.path.join(os.getcwd(), "src"))

async def _find_paths_bfs_legacy(session, source_id: int, target_id: int, max_depth: int) -> List[Dict[str, Any]]:
    """
    Simulates the unoptimized BFS path finding with N+1 query issue.
    """
    queue = [(source_id, [source_id], [], 0)]
    found_paths = []

    while queue:
        current_id, path_ids, path_rels, depth = queue.pop(0)

        if current_id == target_id:
            found_paths.append((path_ids, path_rels))
            if len(found_paths) >= 10:
                break
            continue

        if depth >= max_depth:
            continue

        # --- N+1 QUERY PATTERN START ---
        stmt = text("""
            SELECT r.target_id, r.relation, e.name
            FROM kg_relations r
            JOIN kg_entities e ON r.target_id = e.id
            WHERE r.source_id = :source_id
        """)
        result = await session.execute(stmt, {"source_id": current_id})
        rows = result.fetchall()
        # --- N+1 QUERY PATTERN END ---

        for row in rows:
            tid, rel, tname = row
            if tid not in path_ids:
                queue.append((tid, path_ids + [tid], path_rels + [rel], depth + 1))

    final_paths = []
    all_ids = set()
    for ids, _ in found_paths:
        all_ids.update(ids)

    if not all_ids:
        return []

    id_list = list(all_ids)
    id_str = ",".join(str(i) for i in id_list)
    if not id_str:
        return []

    name_res = await session.execute(text(f"SELECT id, name FROM kg_entities WHERE id IN ({id_str})"))
    id_to_name = {r[0]: r[1] for r in name_res.fetchall()}

    for ids, rels in found_paths:
        nodes = [id_to_name.get(i, "Unknown") for i in ids]
        final_paths.append({
            "nodes": nodes,
            "relations": rels,
            "length": len(rels),
            "confidence": 1.0
        })

    return final_paths

async def run_benchmark():
    # Setup mocks for dependencies not installed in minimal test env
    mock_modules = {}

    mock_lc_core = types.ModuleType("langchain_core")
    mock_lc_core.__path__ = []
    mock_modules["langchain_core"] = mock_lc_core
    mock_modules["langchain_core.documents"] = MagicMock()
    mock_modules["langchain_core.embeddings"] = MagicMock()
    mock_modules["langchain_core.vectorstores"] = MagicMock()
    mock_modules["langchain_core.prompts"] = MagicMock()
    mock_modules["langchain_core.runnables"] = MagicMock()
    mock_modules["langchain_core.output_parsers"] = MagicMock()

    mock_lc_comm = types.ModuleType("langchain_community")
    mock_modules["langchain_community"] = mock_lc_comm
    mock_modules["langchain_community.vectorstores"] = MagicMock()
    mock_modules["langchain_community.embeddings"] = MagicMock()

    mock_pgvector = types.ModuleType("pgvector")
    mock_pgvector.__path__ = []
    mock_modules["pgvector"] = mock_pgvector
    mock_modules["pgvector.sqlalchemy"] = MagicMock()

    mock_redis = types.ModuleType("redis")
    mock_redis.__path__ = []
    mock_modules["redis"] = mock_redis
    mock_modules["redis.asyncio"] = MagicMock()

    with patch.dict(sys.modules, mock_modules):
        # Import inside the patched context
        from ippoc.mnemosyne.graph.manager import GraphManager

        db_url = "sqlite+aiosqlite:///:memory:"
        gm = GraphManager(db_url=db_url)
        await gm.init_db()

        print("Populating graph with synthetic data...")
        chain_len = 20
        branching_factor = 5

        async with gm.Session() as session:
            for i in range(chain_len):
                await session.execute(text("INSERT INTO kg_entities (name, type) VALUES (:n, 'Concept')"), {"n": f"N{i}"})

            for i in range(chain_len - 1):
                res_s = await session.execute(text("SELECT id FROM kg_entities WHERE name=:n"), {"n": f"N{i}"})
                sid = res_s.scalar()
                res_t = await session.execute(text("SELECT id FROM kg_entities WHERE name=:n"), {"n": f"N{i+1}"})
                tid = res_t.scalar()

                await session.execute(text("INSERT INTO kg_relations (source_id, target_id, relation) VALUES (:s, :t, 'next')"), {"s": sid, "t": tid})

                for b in range(branching_factor):
                    d_name = f"D{i}_{b}"
                    await session.execute(text("INSERT INTO kg_entities (name, type) VALUES (:n, 'Distractor')"), {"n": d_name})
                    res_d = await session.execute(text("SELECT id FROM kg_entities WHERE name=:n"), {"n": d_name})
                    did = res_d.scalar()
                    await session.execute(text("INSERT INTO kg_relations (source_id, target_id, relation) VALUES (:s, :t, 'noise')"), {"s": sid, "t": did})

            await session.commit()

        print(f"Graph populated: Chain length {chain_len}, Branching factor {branching_factor}")
        print("Running benchmarks...")

        source = "N0"
        target = f"N{chain_len-1}"

        # 1. Benchmark Optimized CTE
        start_cte = time.time()
        iterations = 50
        for _ in range(iterations):
            await gm.find_relationship_path(source, target, max_depth=chain_len + 5)
        end_cte = time.time()
        avg_cte = (end_cte - start_cte) / iterations

        print(f"CTE (Optimized) Average Time: {avg_cte:.6f}s")

        # 2. Benchmark Legacy BFS
        start_bfs = time.time()
        async with gm.Session() as session:
            res_s = await session.execute(text("SELECT id FROM kg_entities WHERE name=:n"), {"n": source})
            sid = res_s.scalar()
            res_t = await session.execute(text("SELECT id FROM kg_entities WHERE name=:n"), {"n": target})
            tid = res_t.scalar()

            for _ in range(iterations):
                 await _find_paths_bfs_legacy(session, sid, tid, max_depth=chain_len + 5)

        end_bfs = time.time()
        avg_bfs = (end_bfs - start_bfs) / iterations

        print(f"BFS (Legacy) Average Time:    {avg_bfs:.6f}s")

        speedup = avg_bfs / avg_cte if avg_cte > 0 else 0
        print(f"Speedup: {speedup:.2f}x")

        if speedup > 1.5:
            print("SUCCESS: CTE optimization is significantly faster.")
        else:
            print("WARNING: CTE optimization is not showing expected speedup.")

if __name__ == "__main__":
    asyncio.run(run_benchmark())
