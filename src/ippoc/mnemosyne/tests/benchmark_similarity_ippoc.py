import asyncio
import sys
import os
import time
import random
import importlib.util
from sqlalchemy import text
from datetime import datetime

# Function to load GraphManager from specific file path
def load_graph_manager(file_path):
    spec = importlib.util.spec_from_file_location("manager", file_path)
    module = importlib.util.module_from_spec(spec)
    sys.modules["manager"] = module
    spec.loader.exec_module(module)
    return module.GraphManager

async def run_benchmark():
    # Path to the manager file
    manager_path = os.path.join(os.getcwd(), "src/ippoc/mnemosyne/graph/manager.py")
    GraphManager = load_graph_manager(manager_path)

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
        target_entities = []
        for i in range(10):
            target_name = f"T{i}"
            target_entities.append(f"('{target_name}', 'Concept')")

        await session.execute(text(f"INSERT INTO kg_entities (name, type) VALUES {', '.join(target_entities)}"))

        # Get T IDs
        res = await session.execute(text("SELECT id FROM kg_entities WHERE name LIKE 'T%'"))
        t_ids = [row[0] for row in res.fetchall()]

        # Insert relations for A -> T
        a_rels = []
        for tid in t_ids:
            a_rels.append(f"({a_id}, {tid}, 'rel')")

        await session.execute(text(f"INSERT INTO kg_relations (source_id, target_id, relation) VALUES {', '.join(a_rels)}"))

        # Create 100 Similar Entities (S{i})
        # Each shares 5 relations with A (T0..T4) and has 5 unique relations
        s_values = [f"('S{i}', 'Concept')" for i in range(100)]
        await session.execute(text(f"INSERT INTO kg_entities (name, type) VALUES {', '.join(s_values)}"))

        res = await session.execute(text("SELECT id FROM kg_entities WHERE name LIKE 'S%'"))
        s_ids = [row[0] for row in res.fetchall()]

        # Shared relations for S entities
        s_rels = []
        for sid in s_ids:
            # Shared with A (first 5 T's)
            for tid in t_ids[:5]:
                s_rels.append(f"({sid}, {tid}, 'rel')")

            if len(s_rels) > 500:
                await session.execute(text(f"INSERT INTO kg_relations (source_id, target_id, relation) VALUES {', '.join(s_rels)}"))
                s_rels = []

        if s_rels:
            await session.execute(text(f"INSERT INTO kg_relations (source_id, target_id, relation) VALUES {', '.join(s_rels)}"))

        # Create 10,000 Unrelated Entities (N{i})
        print("Inserting 10,000 unrelated entities...")
        unrelated_names = [f"N{i}" for i in range(10000)]
        chunk_size = 500
        for i in range(0, len(unrelated_names), chunk_size):
            chunk = unrelated_names[i:i+chunk_size]
            values = ", ".join([f"('{n}', 'Concept')" for n in chunk])
            await session.execute(text(f"INSERT INTO kg_entities (name, type) VALUES {values}"))

        # Get N IDs
        res = await session.execute(text("SELECT id FROM kg_entities WHERE name LIKE 'N%'"))
        n_ids = [row[0] for row in res.fetchall()]

        # Create 100 random targets X{k}
        x_names = [f"X{i}" for i in range(100)]
        values = ", ".join([f"('{n}', 'Concept')" for n in x_names])
        await session.execute(text(f"INSERT INTO kg_entities (name, type) VALUES {values}"))
        res = await session.execute(text("SELECT id FROM kg_entities WHERE name LIKE 'X%'"))
        x_ids = [row[0] for row in res.fetchall()]

        # Link N entities to X entities
        rel_values = []
        for nid in n_ids:
            targets = random.sample(x_ids, 5)
            for tid in targets:
                rel_values.append(f"({nid}, {tid}, 'rel')")

            if len(rel_values) > 500:
                await session.execute(text(f"INSERT INTO kg_relations (source_id, target_id, relation) VALUES {', '.join(rel_values)}"))
                rel_values = []

        if rel_values:
            await session.execute(text(f"INSERT INTO kg_relations (source_id, target_id, relation) VALUES {', '.join(rel_values)}"))

        await session.commit()

    print("Database populated.")

    # Warmup
    await gm.find_similar_entities("A", similarity_threshold=0.1)

    # Measure
    print("Running benchmark (5 iterations)...")
    start_time = time.time()
    iterations = 5
    for _ in range(iterations):
        results = await gm.find_similar_entities("A", similarity_threshold=0.1)
        if len(results) < 100:
            print(f"Warning: Found only {len(results)} similar entities")

    end_time = time.time()
    avg_time = (end_time - start_time) / iterations

    print(f"Average execution time: {avg_time:.4f} seconds")

if __name__ == "__main__":
    asyncio.run(run_benchmark())
