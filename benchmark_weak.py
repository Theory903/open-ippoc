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
    sys.path.insert(0, str(Path(__file__).parent))
    from src.ippoc.mnemosyne.graph.manager import GraphManager

async def run_benchmark():
    db_url = "sqlite+aiosqlite:///:memory:"
    gm = GraphManager(db_url=db_url)
    await gm.init_db()

    print("Populating database...")
    async with gm.Session() as session:
        # Reference entity A
        await session.execute(text("INSERT INTO kg_entities (name, type) VALUES ('A', 'Concept')"))
        res = await session.execute(text("SELECT id FROM kg_entities WHERE name='A'"))
        a_id = res.scalar()

        # A has 10 relations (T0..T9)
        for i in range(10):
            target_name = f"T{i}"
            await session.execute(text(f"INSERT INTO kg_entities (name, type) VALUES ('{target_name}', 'Concept')"))
            res = await session.execute(text(f"SELECT id FROM kg_entities WHERE name='{target_name}'"))
            t_id = res.scalar()
            await session.execute(text(f"INSERT INTO kg_relations (source_id, target_id, relation) VALUES ({a_id}, {t_id}, 'rel')"))

        # Create 5000 weak candidates
        # Each shares only 1 relation with A (e.g. T0), and has 20 unique relations
        print("Inserting 5000 weak candidates...")
        res = await session.execute(text(f"SELECT id FROM kg_entities WHERE name='T0'"))
        t0_id = res.scalar()

        names = [f"W{i}" for i in range(5000)]
        chunk_size = 500
        for i in range(0, len(names), chunk_size):
            chunk = names[i:i+chunk_size]
            values = ", ".join([f"('{n}', 'Concept')" for n in chunk])
            await session.execute(text(f"INSERT INTO kg_entities (name, type) VALUES {values}"))

        res = await session.execute(text("SELECT id FROM kg_entities WHERE name LIKE 'W%'"))
        w_ids = [row[0] for row in res.fetchall()]

        rel_values = []
        # shared relation
        for wid in w_ids:
            rel_values.append(f"({wid}, {t0_id}, 'rel')")

            # Since we just want to create work for total_cnt, we can link them to some random other entities
            # We don't necessarily need unique targets, just lots of relations
            for k in range(20):
                # arbitrary target id, say k+1
                rel_values.append(f"({wid}, {k%10 + 1}, 'other_rel')")

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
    await gm.find_similar_entities("A", similarity_threshold=0.5)

    # Measure
    start_time = time.time()
    iterations = 10
    results = []
    for _ in range(iterations):
        results = await gm.find_similar_entities("A", similarity_threshold=0.5)

    end_time = time.time()
    avg_time = (end_time - start_time) / iterations

    print(f"Average execution time: {avg_time:.4f} seconds")

if __name__ == "__main__":
    asyncio.run(run_benchmark())
