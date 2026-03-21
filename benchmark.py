import asyncio
import time
import sys
import os

# Set PYTHONPATH to load the local codebase modules properly without triggering circular/deep imports if not needed
sys.path.insert(0, os.path.abspath('src/ippoc'))

# Instead of importing the full system, just import the file we care about since it has minimal dependencies
import importlib.util
spec = importlib.util.spec_from_file_location("manager", "src/ippoc/mnemosyne/graph/manager.py")
manager_module = importlib.util.module_from_spec(spec)
sys.modules["mnemosyne.graph.manager"] = manager_module
spec.loader.exec_module(manager_module)

GraphManager = manager_module.GraphManager

async def setup_data(mgr: GraphManager):
    await mgr.init_db()

    # Create a dense graph to benchmark
    # A -> B1..B10 -> C1..C10 -> D
    # Lots of branches
    for i in range(10):
        await mgr.add_triple("A", f"rel1_{i}", f"B{i}")
        for j in range(10):
            await mgr.add_triple(f"B{i}", f"rel2_{j}", f"C{j}")
    for j in range(10):
        await mgr.add_triple(f"C{j}", "rel3", "D")

async def run_benchmark():
    # Use in-memory SQLite for testing
    mgr = GraphManager("sqlite+aiosqlite:///:memory:")
    await setup_data(mgr)

    # Test optimized CTE approach (current)
    start = time.perf_counter()
    paths = await mgr.find_relationship_path("A", "D", max_depth=3)
    end = time.perf_counter()

    duration = end - start
    print(f"CTE Path finding took {duration:.4f} seconds, found {len(paths)} paths.")

if __name__ == "__main__":
    asyncio.run(run_benchmark())
