import asyncio
import sys
import os
import time
import types
from pathlib import Path
from unittest.mock import MagicMock
from sqlalchemy import text

# Mock missing dependencies
# Helper to mock package structure
def mock_package(name):
    m = types.ModuleType(name)
    m.__path__ = []
    sys.modules[name] = m
    return m

mock_package("langchain_core")
sys.modules["langchain_core.documents"] = MagicMock()
sys.modules["langchain_core.embeddings"] = MagicMock()
sys.modules["langchain_core.vectorstores"] = MagicMock()
sys.modules["langchain_core.prompts"] = MagicMock()
sys.modules["langchain_core.runnables"] = MagicMock()
sys.modules["langchain_core.output_parsers"] = MagicMock()
sys.modules["langchain_core.language_models"] = MagicMock()

mock_package("langchain_community")
sys.modules["langchain_community.vectorstores"] = MagicMock()

mock_package("langchain_google_genai")

sys.modules["pgvector"] = MagicMock()
sys.modules["pgvector.sqlalchemy"] = MagicMock()
sys.modules["redis"] = MagicMock()
sys.modules["redis.asyncio"] = MagicMock()

# Add infra/src to python path
sys.path.insert(0, str(Path(__file__).parent.parent.parent))

try:
    from mnemosyne.graph.manager import GraphManager
except ImportError:
    sys.path.insert(0, str(Path(__file__).parent.parent))
    from mnemosyne.graph.manager import GraphManager

async def run_benchmark():
    # Use in-memory SQLite for speed and isolation
    db_url = "sqlite+aiosqlite:///:memory:"
    gm = GraphManager(db_url=db_url)
    await gm.init_db()

    print("Populating database with a dense cyclic graph...")

    # We will create a grid-like structure (mesh) where each node connects to neighbors.
    # Grid size 20x20 = 400 nodes.
    # Each node (i, j) connects to (i+1, j), (i, j+1), (i-1, j), (i, j-1) if within bounds.
    # This creates many cycles.

    width = 20
    height = 20

    async with gm.Session() as session:
        # Create entities
        print(f"Creating {width*height} entities...")
        entities = []
        for r in range(height):
            for c in range(width):
                name = f"N_{r}_{c}"
                entities.append(f"('{name}', 'Node')")

        # Batch insert entities
        chunk_size = 500
        for i in range(0, len(entities), chunk_size):
            chunk = entities[i:i+chunk_size]
            values = ", ".join(chunk)
            await session.execute(text(f"INSERT INTO kg_entities (name, type) VALUES {values}"))

        # Get IDs mapping
        res = await session.execute(text("SELECT name, id FROM kg_entities"))
        name_to_id = {row[0]: row[1] for row in res.fetchall()}

        # Create relations
        print("Creating relations...")
        relations = []
        for r in range(height):
            for c in range(width):
                src_name = f"N_{r}_{c}"
                src_id = name_to_id[src_name]

                # Neighbors: up, down, left, right
                neighbors = []
                if r > 0: neighbors.append((r-1, c))
                if r < height-1: neighbors.append((r+1, c))
                if c > 0: neighbors.append((r, c-1))
                if c < width-1: neighbors.append((r, c+1))

                # Add diagonal connections to increase density and cycles
                if r > 0 and c > 0: neighbors.append((r-1, c-1))
                if r < height-1 and c < width-1: neighbors.append((r+1, c+1))

                for nr, nc in neighbors:
                    tgt_name = f"N_{nr}_{nc}"
                    tgt_id = name_to_id[tgt_name]
                    relations.append(f"({src_id}, {tgt_id}, 'connects_to')")

        # Batch insert relations
        # SQLite limits variables, so keep chunks reasonable
        chunk_size = 500
        total_rels = len(relations)
        print(f"Inserting {total_rels} relations...")
        for i in range(0, total_rels, chunk_size):
            chunk = relations[i:i+chunk_size]
            values = ", ".join(chunk)
            await session.execute(text(f"INSERT INTO kg_relations (source_id, target_id, relation) VALUES {values}"))

        await session.commit()

    print("Database populated.")
    print("Running pathfinding benchmark...")

    # Test path from top-left to near-middle
    start_node = "N_0_0"
    end_node = "N_4_4"

    # Warmup
    print("Warmup run...")
    await gm.find_relationship_path(start_node, end_node, max_depth=5)

    # Benchmark
    iterations = 20
    max_depth = 6 # Deep enough to encounter many cycles in grid

    print(f"Benchmarking pathfinding from {start_node} to {end_node} with max_depth={max_depth} over {iterations} iterations...")

    start_time = time.time()
    total_paths = 0

    for i in range(iterations):
        paths = await gm.find_relationship_path(start_node, end_node, max_depth=max_depth)
        total_paths += len(paths)

    end_time = time.time()
    avg_time = (end_time - start_time) / iterations
    avg_paths = total_paths / iterations

    print(f"Average execution time: {avg_time:.6f} seconds")
    print(f"Average paths found: {avg_paths}")

    return avg_time

if __name__ == "__main__":
    asyncio.run(run_benchmark())
