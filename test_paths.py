import asyncio
import sys
import os
from pathlib import Path
from sqlalchemy import text

sys.path.insert(0, str(Path(__file__).parent / "src"))

try:
    from ippoc.mnemosyne.graph.manager import GraphManager
except ImportError as e:
    sys.path.insert(0, str(Path(__file__).parent))
    from src.ippoc.mnemosyne.graph.manager import GraphManager

async def run_test():
    db_url = "sqlite+aiosqlite:///:memory:"
    gm = GraphManager(db_url=db_url)
    await gm.init_db()

    async with gm.Session() as session:
        for n in ["A", "B", "C", "D"]:
            await session.execute(text(f"INSERT INTO kg_entities (name, type) VALUES ('{n}', 'Concept')"))

        # A -> B -> C -> D
        await session.execute(text("INSERT INTO kg_relations (source_id, target_id, relation) VALUES (1, 2, 'rel1')"))
        await session.execute(text("INSERT INTO kg_relations (source_id, target_id, relation) VALUES (2, 3, 'rel2')"))
        await session.execute(text("INSERT INTO kg_relations (source_id, target_id, relation) VALUES (3, 4, 'rel3')"))

        # A -> D
        await session.execute(text("INSERT INTO kg_relations (source_id, target_id, relation) VALUES (1, 4, 'rel4')"))

        await session.commit()

    results = await gm.find_relationship_path("A", "D", max_depth=3)
    for r in results:
        print(r)

if __name__ == "__main__":
    asyncio.run(run_test())
