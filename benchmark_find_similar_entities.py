import asyncio
import time
import os
import sys

# Ensure src is in path
sys.path.append(os.path.join(os.getcwd(), "src"))

from ippoc.mnemosyne.graph.manager import GraphManager

async def main():
    db_url = "sqlite+aiosqlite:///:memory:"
    gm = GraphManager(db_url=db_url)
    await gm.init_db()

    print("Adding dummy data...")
    # Add a central entity and lots of relations
    for i in range(100):
        await gm.add_triple("CentralEntity", f"rel_{i}", f"Target_{i}")

    # Add many other entities that share some relations
    for i in range(500):
        await gm.add_triple(f"OtherEntity_{i}", f"rel_{i % 10}", f"Target_{i % 10}")
        await gm.add_triple(f"OtherEntity_{i}", f"rel_{i % 20}", f"Target_{i % 20}")
        await gm.add_triple(f"OtherEntity_{i}", f"unique_rel_{i}", f"UniqueTarget_{i}")

    print("Benchmarking find_similar_entities...")
    start_time = time.time()
    for _ in range(10):
        results = await gm.find_similar_entities("CentralEntity", similarity_threshold=0.01)
    end_time = time.time()

    print(f"Results found: {len(results)}")
    print(f"Time taken (10 runs): {end_time - start_time:.4f} seconds")

if __name__ == "__main__":
    asyncio.run(main())
