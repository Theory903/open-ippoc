import asyncio
import sys
import os
import time
import random
from pathlib import Path
from sqlalchemy import text

sys.path.insert(0, str(Path(__file__).parent / "src"))

try:
    from ippoc.mnemosyne.graph.manager import GraphManager
except ImportError as e:
    sys.path.insert(0, str(Path(__file__).parent))
    from src.ippoc.mnemosyne.graph.manager import GraphManager

async def run_benchmark():
    db_url = "sqlite+aiosqlite:///:memory:"
    gm = GraphManager(db_url=db_url)
    await gm.init_db()

    print("Populating dense cyclic graph (K5)...")

    # Create K5 complete graph (every node connected to every other node)
    nodes = [f"N{i}" for i in range(5)]
    async with gm.Session() as session:
        for n in nodes:
            await session.execute(text(f"INSERT INTO kg_entities (name, type) VALUES ('{n}', 'Concept')"))

        # Add edges in both directions
        for i in range(5):
            for j in range(5):
                if i != j:
                    # id is 1-indexed in sqlite autoincrement here
                    await session.execute(text(f"INSERT INTO kg_relations (source_id, target_id, relation) VALUES ({i+1}, {j+1}, 'connected_to')"))
        await session.commit()

    print("Running benchmark...")

    # Measure
    start_time = time.time()
    iterations = 5
    # Find paths from N0 to N4 with depth 9
    for _ in range(iterations):
        results = await gm.find_relationship_path("N0", "N4", max_depth=9)
    end_time = time.time()

    avg_time = (end_time - start_time) / iterations
    print(f"Average execution time: {avg_time:.4f} seconds")
    print(f"Results count: {len(results)}")

if __name__ == "__main__":
    asyncio.run(run_benchmark())
