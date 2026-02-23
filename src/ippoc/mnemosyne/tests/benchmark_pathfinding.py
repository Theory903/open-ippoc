
import sys
import os
import asyncio
import time
import logging
import random

# Ensure src is in path
sys.path.append(os.path.join(os.getcwd(), "src"))

try:
    from ippoc.mnemosyne.graph.manager import GraphManager
except ImportError:
    # Try importing directly if package structure is complex
    sys.path.append(os.path.join(os.getcwd(), "src", "ippoc"))
    from mnemosyne.graph.manager import GraphManager

# Configure logging to hide noisy output
logging.basicConfig(level=logging.ERROR)
logger = logging.getLogger(__name__)

async def setup_grid_graph(gm, width=5, height=5):
    """
    Creates a grid graph where each node (x,y) connects to its 4 neighbors.
    This creates many cycles.
    """
    await gm.init_db()

    # Add nodes and edges
    for x in range(width):
        for y in range(height):
            current = f"Node_{x}_{y}"
            neighbors = []
            if x > 0: neighbors.append(f"Node_{x-1}_{y}")
            if x < width - 1: neighbors.append(f"Node_{x+1}_{y}")
            if y > 0: neighbors.append(f"Node_{x}_{y-1}")
            if y < height - 1: neighbors.append(f"Node_{x}_{y+1}")

            for neighbor in neighbors:
                # Add bidirectional edges
                await gm.add_triple(current, "connected_to", neighbor)

async def run_benchmark():
    # Use in-memory SQLite for speed and isolation
    db_url = "sqlite+aiosqlite:///:memory:"
    gm = GraphManager(db_url=db_url)

    print("Setting up 5x5 grid graph (highly cyclic)...")
    start_setup = time.time()
    await setup_grid_graph(gm, width=5, height=5)
    print(f"Graph setup took {time.time() - start_setup:.4f}s")

    # Measure pathfinding
    # From (0,0) to (4,4) - max depth 8 (Manhattan distance is 8)
    source = "Node_0_0"
    target = "Node_4_4"
    max_depth = 10
    iterations = 20

    print(f"Benchmarking pathfinding from {source} to {target} (max_depth={max_depth})...")

    times = []
    for i in range(iterations):
        start = time.time()
        paths = await gm.find_relationship_path(source, target, max_depth=max_depth)
        duration = time.time() - start
        times.append(duration)
        print(f"Run {i+1}: {duration:.4f}s, paths found: {len(paths)}")

    avg_time = sum(times) / len(times)
    min_time = min(times)
    max_time = max(times)

    print("\n--- Results ---")
    print(f"Average Time: {avg_time:.4f}s")
    print(f"Min Time:     {min_time:.4f}s")
    print(f"Max Time:     {max_time:.4f}s")

    return avg_time

if __name__ == "__main__":
    asyncio.run(run_benchmark())
