import asyncio
import sys
import os
import time
import random
import importlib.util
from sqlalchemy import text
from datetime import datetime

# Import GraphManager using importlib to avoid package initialization issues
spec = importlib.util.spec_from_file_location("manager", "src/ippoc/mnemosyne/graph/manager.py")
manager_module = importlib.util.module_from_spec(spec)
sys.modules["manager"] = manager_module
spec.loader.exec_module(manager_module)
GraphManager = manager_module.GraphManager

async def run_benchmark():
    # Use in-memory SQLite for speed and isolation
    db_url = "sqlite+aiosqlite:///:memory:"
    gm = GraphManager(db_url=db_url)
    await gm.init_db()

    print(f"[{datetime.now()}] Populating database...")

    async with gm.Session() as session:
        # Create Target Entity "A"
        await session.execute(text("INSERT INTO kg_entities (name, type) VALUES ('A', 'Concept')"))
        res = await session.execute(text("SELECT id FROM kg_entities WHERE name='A'"))
        a_id = res.scalar()

        # Create 10 relations for A: (A) -> r{i} -> T{i}
        # Use diverse relations
        relations_pool = [f"rel_{k}" for k in range(50)]

        a_relations = []
        for i in range(10):
            target_name = f"T{i}"
            rel_name = relations_pool[i % len(relations_pool)] # varied relations
            a_relations.append((target_name, rel_name))

            await session.execute(text(f"INSERT INTO kg_entities (name, type) VALUES ('{target_name}', 'Concept')"))
            res = await session.execute(text(f"SELECT id FROM kg_entities WHERE name='{target_name}'"))
            t_id = res.scalar()
            await session.execute(text(f"INSERT INTO kg_relations (source_id, target_id, relation) VALUES ({a_id}, {t_id}, '{rel_name}')"))

        # Create 100 Similar Entities (S{i})
        # Each shares 5 relations with A (T0..T4) and has 5 unique relations
        s_values = []
        for i in range(100):
            s_name = f"S{i}"
            s_values.append(f"('{s_name}', 'Concept')")

        await session.execute(text(f"INSERT INTO kg_entities (name, type) VALUES {', '.join(s_values)}"))

        # Get IDs for S entities
        res = await session.execute(text("SELECT id, name FROM kg_entities WHERE name LIKE 'S%'"))
        s_map = {row.name: row.id for row in res.fetchall()}

        # Get IDs for T entities
        res = await session.execute(text("SELECT id, name FROM kg_entities WHERE name LIKE 'T%'"))
        t_map = {row.name: row.id for row in res.fetchall()}

        rel_values = []
        u_ent_values = []

        for i in range(100):
            s_name = f"S{i}"
            s_id = s_map[s_name]

            # Shared relations (T0..T4) matches A's relations
            for j in range(5):
                t_name, rel_name = a_relations[j]
                t_id = t_map[t_name]
                rel_values.append(f"({s_id}, {t_id}, '{rel_name}')")

            # Unique relations (U{i}_{j})
            for j in range(5):
                u_name = f"U{i}_{j}"
                u_ent_values.append(f"('{u_name}', 'Concept')")

        # Batch insert U entities
        chunk_size = 500
        for i in range(0, len(u_ent_values), chunk_size):
            chunk = u_ent_values[i:i+chunk_size]
            await session.execute(text(f"INSERT INTO kg_entities (name, type) VALUES {', '.join(chunk)}"))

        # Get U IDs
        res = await session.execute(text("SELECT id FROM kg_entities WHERE name LIKE 'U%'"))
        u_ids = [row.id for row in res.fetchall()]

        # Add U relations
        u_rel_values = []
        s_ids_list = list(s_map.values())
        u_idx = 0
        for i, s_id in enumerate(s_ids_list):
            for j in range(5):
                if u_idx < len(u_ids):
                    rel_name = random.choice(relations_pool)
                    u_rel_values.append(f"({s_id}, {u_ids[u_idx]}, '{rel_name}')")
                    u_idx += 1

        all_rels = rel_values + u_rel_values
        for i in range(0, len(all_rels), chunk_size):
            chunk = all_rels[i:i+chunk_size]
            await session.execute(text(f"INSERT INTO kg_relations (source_id, target_id, relation) VALUES {', '.join(chunk)}"))

        # Create 10,000 Unrelated Entities (N{i})
        print(f"[{datetime.now()}] Inserting 10,000 unrelated entities...")

        n_values = [f"('N{i}', 'Concept')" for i in range(10000)]
        for i in range(0, len(n_values), chunk_size):
            chunk = n_values[i:i+chunk_size]
            await session.execute(text(f"INSERT INTO kg_entities (name, type) VALUES {', '.join(chunk)}"))

        # Get N IDs
        res = await session.execute(text("SELECT id FROM kg_entities WHERE name LIKE 'N%'"))
        n_ids = [row.id for row in res.fetchall()]

        # Insert relations for N entities to some random X targets
        x_values = [f"('X{i}', 'Concept')" for i in range(100)]
        await session.execute(text(f"INSERT INTO kg_entities (name, type) VALUES {', '.join(x_values)}"))

        res = await session.execute(text("SELECT id FROM kg_entities WHERE name LIKE 'X%'"))
        x_ids = [row.id for row in res.fetchall()]

        n_rel_values = []
        for nid in n_ids:
            # Pick 5 random x_ids
            targets = random.sample(x_ids, 5)
            for tid in targets:
                rel_name = random.choice(relations_pool)
                n_rel_values.append(f"({nid}, {tid}, '{rel_name}')")

        print(f"[{datetime.now()}] Inserting {len(n_rel_values)} relations...")
        for i in range(0, len(n_rel_values), chunk_size):
            chunk = n_rel_values[i:i+chunk_size]
            await session.execute(text(f"INSERT INTO kg_relations (source_id, target_id, relation) VALUES {', '.join(chunk)}"))

        await session.commit()

    print(f"[{datetime.now()}] Database populated.")
    print("Running benchmark...")

    # Warmup
    await gm.find_similar_entities("A", similarity_threshold=0.1)

    # Measure
    start_time = time.time()
    iterations = 5
    for _ in range(iterations):
        results = await gm.find_similar_entities("A", similarity_threshold=0.1)

    end_time = time.time()
    avg_time = (end_time - start_time) / iterations

    print(f"Average execution time: {avg_time:.4f} seconds")
    if results:
        print(f"Results count: {len(results)}")
    else:
        print("No results found!")

if __name__ == "__main__":
    asyncio.run(run_benchmark())
