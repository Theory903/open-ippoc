import asyncio
import sys
import os
import time
import random
from pathlib import Path
from sqlalchemy import text

# Add src to python path so we can import src.ippoc...
sys.path.insert(0, str(Path(__file__).parent / "src"))

try:
    from ippoc.mnemosyne.graph.manager import GraphManager
except ImportError as e:
    print(f"Failed to import GraphManager: {e}")
    # Try alternate path structure just in case
    sys.path.insert(0, str(Path(__file__).parent))
    from src.ippoc.mnemosyne.graph.manager import GraphManager

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
        print("Inserting 10,000 unrelated entities...")

        # Optimizing bulk insert
        unrelated_names = [f"N{i}" for i in range(10000)]
        chunk_size = 500
        for i in range(0, len(unrelated_names), chunk_size):
            chunk = unrelated_names[i:i+chunk_size]
            values = ", ".join([f"('{n}', 'Concept')" for n in chunk])
            await session.execute(text(f"INSERT INTO kg_entities (name, type) VALUES {values}"))

        res = await session.execute(text("SELECT id FROM kg_entities WHERE name LIKE 'N%'"))
        n_ids = [row[0] for row in res.fetchall()]

        # Insert relations for N entities
        x_names = [f"X{i}" for i in range(100)]
        values = ", ".join([f"('{n}', 'Concept')" for n in x_names])
        await session.execute(text(f"INSERT INTO kg_entities (name, type) VALUES {values}"))
        res = await session.execute(text("SELECT id FROM kg_entities WHERE name LIKE 'X%'"))
        x_ids = [row[0] for row in res.fetchall()]

        rel_values = []
        for nid in n_ids:
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
    results = []
    for _ in range(iterations):
        results = await gm.find_similar_entities("A", similarity_threshold=0.1)
        if len(results) < 100:
            print(f"Warning: Found only {len(results)} similar entities")

    end_time = time.time()
    avg_time = (end_time - start_time) / iterations

    print(f"Average execution time: {avg_time:.4f} seconds")
    print(f"Results count: {len(results)}")

    # Verify correctness
    # S0..S99 should be in results
    found_names = {r['entity'] for r in results}
    missing = [f"S{i}" for i in range(100) if f"S{i}" not in found_names]
    if missing:
        print(f"FAILED: Missing expected entities: {missing[:10]}...")
    else:
        print("SUCCESS: All expected entities found.")

if __name__ == "__main__":
    asyncio.run(run_benchmark())
