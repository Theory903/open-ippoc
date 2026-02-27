import asyncio
import sys
import os
import time
from pathlib import Path
from sqlalchemy import text

sys.path.insert(0, str(Path(__file__).parent / "src"))

try:
    from ippoc.mnemosyne.graph.manager import GraphManager
except ImportError as e:
    sys.path.insert(0, str(Path(__file__).parent))
    from src.ippoc.mnemosyne.graph.manager import GraphManager

async def run_test():
    db_url = "sqlite+aiosqlite:///:memory:"
    gm = GraphManager(db_url=db_url)
    await gm.init_db()

    print("Populating dense cyclic graph (K5)...")

    nodes = [f"N{i}" for i in range(5)]
    async with gm.Session() as session:
        for n in nodes:
            await session.execute(text(f"INSERT INTO kg_entities (name, type) VALUES ('{n}', 'Concept')"))

        for i in range(5):
            for j in range(5):
                if i != j:
                    await session.execute(text(f"INSERT INTO kg_relations (source_id, target_id, relation) VALUES ({i+1}, {j+1}, 'connected_to')"))
        await session.commit()

    print("Running optimized benchmark...")

    # Measure original
    start_time = time.time()
    iterations = 5
    for _ in range(iterations):
        results = await gm.find_relationship_path("N0", "N4", max_depth=9)
    end_time = time.time()

    avg_time = (end_time - start_time) / iterations
    print(f"Original average execution time: {avg_time:.4f} seconds")
    print(f"Original results count: {len(results)}")

    # Patch
    old_cte = gm._find_paths_cte

    async def fast_cte(session, source_id, target_id, max_depth):
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
                -- IN-SQL CYCLE PRUNING
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

        rows = result.fetchall()

        if not rows:
            return []

        # Collect all unique node IDs to fetch names in bulk
        all_node_ids = set()
        parsed_rows = []

        from sqlalchemy import bindparam

        for row in rows:
            ids = [int(x) for x in row[0].split(',')]
            rels = row[1].split(',')

            # The SQL pruning already ensures no cycles!

            all_node_ids.update(ids)
            parsed_rows.append((ids, rels))

        if not parsed_rows:
            return []

        name_stmt = text("SELECT id, name FROM kg_entities WHERE id IN :ids")
        name_stmt = name_stmt.bindparams(bindparam("ids", expanding=True))
        name_res = await session.execute(name_stmt, {"ids": list(all_node_ids)})

        id_to_name = {row.id: row.name for row in name_res}

        paths = []
        for ids, rels in parsed_rows:
            nodes = []
            valid_path = True
            for nid in ids:
                name = id_to_name.get(nid)
                if name is None:
                    valid_path = False
                    break
                nodes.append(name)

            if valid_path:
                paths.append({
                    "nodes": nodes,
                    "relations": rels,
                    "length": len(rels),
                    "confidence": 1.0 - (len(rels) * 0.1)
                })

        return paths

    gm._find_paths_cte = fast_cte

    # Measure patched
    start_time = time.time()
    iterations = 5
    for _ in range(iterations):
        results2 = await gm.find_relationship_path("N0", "N4", max_depth=9)
    end_time = time.time()

    avg_time = (end_time - start_time) / iterations
    print(f"Patched average execution time: {avg_time:.4f} seconds")
    print(f"Patched results count: {len(results2)}")

if __name__ == "__main__":
    asyncio.run(run_test())
