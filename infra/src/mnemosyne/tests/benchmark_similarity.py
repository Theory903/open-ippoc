import asyncio
import sys
import os
import time
import random
from pathlib import Path
from sqlalchemy import text
import importlib.util

# Load GraphManager directly from file to avoid package dependencies
graph_manager_path = Path(__file__).parent.parent / "graph" / "manager.py"
spec = importlib.util.spec_from_file_location("mnemosyne.graph.manager", str(graph_manager_path))
manager_module = importlib.util.module_from_spec(spec)
sys.modules["mnemosyne.graph.manager"] = manager_module
spec.loader.exec_module(manager_module)
GraphManager = manager_module.GraphManager

async def run_benchmark():
    # Use in-memory SQLite for speed and isolation
    db_url = "sqlite+aiosqlite:///:memory:"
    gm = GraphManager(db_url=db_url)
    await gm.init_db()

    print("Populating database...")

    # Batch insert logic to speed up population
    async with gm.Session() as session:
        # Create Target Entity "A"
        await session.execute(text("INSERT INTO kg_entities (name, type) VALUES ('A', 'Concept')"))
        res = await session.execute(text("SELECT id FROM kg_entities WHERE name='A'"))
        a_id = res.scalar()

        # Create 10 relations for A: (A) -> r{i} -> T{i}
        # Create T{i} entities first
        for i in range(10):
            target_name = f"T{i}"
            await session.execute(text(f"INSERT INTO kg_entities (name, type) VALUES ('{target_name}', 'Concept')"))
            res = await session.execute(text(f"SELECT id FROM kg_entities WHERE name='{target_name}'"))
            t_id = res.scalar()
            await session.execute(text(f"INSERT INTO kg_relations (source_id, target_id, relation) VALUES ({a_id}, {t_id}, 'rel')"))

        # Create 100 Similar Entities (S{i})
        # Each shares 5 relations with A (T0..T4) and has 5 unique relations
        for i in range(100):
            s_name = f"S{i}"
            await session.execute(text(f"INSERT INTO kg_entities (name, type) VALUES ('{s_name}', 'Concept')"))
            res = await session.execute(text(f"SELECT id FROM kg_entities WHERE name='{s_name}'"))
            s_id = res.scalar()

            # Shared relations
            for j in range(5):
                target_name = f"T{j}"
                res = await session.execute(text(f"SELECT id FROM kg_entities WHERE name='{target_name}'"))
                t_id = res.scalar()
                await session.execute(text(f"INSERT INTO kg_relations (source_id, target_id, relation) VALUES ({s_id}, {t_id}, 'rel')"))

            # Unique relations (U{i}_{j})
            for j in range(5):
                u_name = f"U{i}_{j}"
                await session.execute(text(f"INSERT INTO kg_entities (name, type) VALUES ('{u_name}', 'Concept')"))
                res = await session.execute(text(f"SELECT id FROM kg_entities WHERE name='{u_name}'"))
                u_id = res.scalar()
                await session.execute(text(f"INSERT INTO kg_relations (source_id, target_id, relation) VALUES ({s_id}, {u_id}, 'rel')"))

        # Create 10,000 Unrelated Entities (N{i})
        # Each has 5 relations to random unique targets
        # To speed up, we can generate SQL directly or use bulk insert if possible.
        # But for 10k it might be okay.
        print("Inserting 10,000 unrelated entities...")

        # Optimizing bulk insert
        # Generate names
        unrelated_names = [f"N{i}" for i in range(10000)]
        # Insert entities
        # SQLite limit is usually 999 variables, so chunk it
        chunk_size = 500
        for i in range(0, len(unrelated_names), chunk_size):
            chunk = unrelated_names[i:i+chunk_size]
            values = ", ".join([f"('{n}', 'Concept')" for n in chunk])
            await session.execute(text(f"INSERT INTO kg_entities (name, type) VALUES {values}"))

        # Get IDs
        # This is tricky without returning * in SQLite consistently or assumptions.
        # Just select all N%
        res = await session.execute(text("SELECT id FROM kg_entities WHERE name LIKE 'N%'"))
        n_ids = [row[0] for row in res.fetchall()]

        # Insert relations for N entities
        # Connect to some random targets X{k}
        # Create 100 random targets
        x_names = [f"X{i}" for i in range(100)]
        values = ", ".join([f"('{n}', 'Concept')" for n in x_names])
        await session.execute(text(f"INSERT INTO kg_entities (name, type) VALUES {values}"))
        res = await session.execute(text("SELECT id FROM kg_entities WHERE name LIKE 'X%'"))
        x_ids = [row[0] for row in res.fetchall()]

        # Link N entities to X entities
        # 5 relations each
        rel_values = []
        for nid in n_ids:
            # Pick 5 random x_ids
            targets = random.sample(x_ids, 5)
            for tid in targets:
                rel_values.append(f"({nid}, {tid}, 'rel')")

            if len(rel_values) > 500:
                v = ", ".join(rel_values)
                await session.execute(text(f"INSERT INTO kg_relations (source_id, target_id, relation) VALUES {v}"))
                rel_values = []

        if rel_values:
            v = ", ".join(rel_values)
            await session.execute(text(f"INSERT INTO kg_relations (source_id, target_id, relation) VALUES {v}"))

        await session.commit()

    print("Database populated.")
    print("Running benchmark...")

    # Warmup
    await gm.find_similar_entities("A", similarity_threshold=0.1)

    # Measure
    start_time = time.time()
    iterations = 5
    for _ in range(iterations):
        results = await gm.find_similar_entities("A", similarity_threshold=0.1)
        # Basic validation
        # Should find at least 100 similar entities
        if len(results) < 100:
            print(f"Warning: Found only {len(results)} similar entities")

    end_time = time.time()
    avg_time = (end_time - start_time) / iterations

    print(f"Average execution time: {avg_time:.4f} seconds")
    print(f"Results count: {len(results)}")

if __name__ == "__main__":
    asyncio.run(run_benchmark())
