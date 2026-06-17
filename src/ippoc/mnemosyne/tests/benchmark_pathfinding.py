import asyncio
import time
import sys
import os
import logging
import importlib.util

# Ensure src is in path so internal relative imports work if needed,
# though we are loading directly.
sys.path.append(os.path.join(os.getcwd(), "src"))

# Manually load GraphManager from file to avoid triggering package __init__
# which loads heavy dependencies like langchain.
file_path = os.path.join(os.getcwd(), "src/ippoc/mnemosyne/graph/manager.py")
spec = importlib.util.spec_from_file_location("ippoc.mnemosyne.graph.manager", file_path)
graph_manager_module = importlib.util.module_from_spec(spec)
sys.modules["ippoc.mnemosyne.graph.manager"] = graph_manager_module
spec.loader.exec_module(graph_manager_module)

GraphManager = graph_manager_module.GraphManager

# Configure logging to suppress noisy output during benchmark
logging.getLogger("ippoc.mnemosyne.graph.manager").setLevel(logging.WARNING)
logging.basicConfig(level=logging.INFO)

async def create_dense_cyclic_graph(gm, size=5):
    """Creates a grid-like graph of size x size with bidirectional edges."""
    print(f"Creating {size}x{size} grid graph...")
    start_time = time.time()
    count = 0
    # Add nodes and edges
    for i in range(size):
        for j in range(size):
            node_name = f"Node_{i}_{j}"
            # Connect to right neighbor
            if j < size - 1:
                right_neighbor = f"Node_{i}_{j+1}"
                await gm.add_triple(node_name, "connects_to", right_neighbor)
                await gm.add_triple(right_neighbor, "connects_to", node_name) # Cycle!
                count += 2
            # Connect to bottom neighbor
            if i < size - 1:
                bottom_neighbor = f"Node_{i+1}_{j}"
                await gm.add_triple(node_name, "connects_to", bottom_neighbor)
                await gm.add_triple(bottom_neighbor, "connects_to", node_name) # Cycle!
                count += 2

    print(f"Graph created with {size*size} nodes and {count} edges in {time.time() - start_time:.4f}s")

async def run_benchmark():
    # Use in-memory SQLite for speed and isolation
    db_url = "sqlite+aiosqlite:///:memory:"
    gm = GraphManager(db_url=db_url)
    await gm.init_db()

    # Create a reasonably complex graph
    # 6x6 grid = 36 nodes. Shortest path (0,0)->(5,5) is 10 steps.
    grid_size = 6
    await create_dense_cyclic_graph(gm, size=grid_size)

    start_node = "Node_0_0"
    end_node = f"Node_{grid_size-1}_{grid_size-1}"

    print(f"Finding paths from {start_node} to {end_node}...")

    # Warmup
    await gm.find_relationship_path(start_node, end_node, max_depth=4)

    # Benchmark
    iterations = 5
    total_time = 0

    # Depth 10 should find the shortest path(s).
    # Without cycle detection, it might explore many looping paths of length <= 10.
    test_depth = 10

    for i in range(iterations):
        t0 = time.time()
        paths = await gm.find_relationship_path(start_node, end_node, max_depth=test_depth)
        dt = time.time() - t0
        total_time += dt
        print(f"Iteration {i+1}: {dt:.4f}s, found {len(paths)} paths")

    avg_time = total_time / iterations
    print(f"\nAverage time: {avg_time:.4f}s")

if __name__ == "__main__":
    asyncio.run(run_benchmark())
