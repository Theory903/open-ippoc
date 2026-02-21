
import pytest
import pytest_asyncio
import sys
import os
import asyncio
from sqlalchemy import event

# Ensure src is in path
sys.path.append(os.path.join(os.getcwd(), "src"))

from ippoc.mnemosyne.graph.manager import GraphManager

@pytest_asyncio.fixture
async def graph_manager():
    # Use in-memory SQLite
    db_url = "sqlite+aiosqlite:///:memory:"
    gm = GraphManager(db_url=db_url)
    await gm.init_db()
    return gm

@pytest.mark.asyncio
async def test_get_entity_context_correctness(graph_manager):
    gm = graph_manager
    # Setup Data
    # Entity: Hero
    # Outgoing: Hero -> attacks -> Villain
    # Incoming: Villager -> praises -> Hero
    # Attribute: Hero -> has_attribute -> Brave

    await gm.add_triple("Hero", "attacks", "Villain")
    await gm.add_triple("Villager", "praises", "Hero")
    await gm.add_triple("Hero", "has_attribute", "Brave")

    # Execute
    context = await gm.get_entity_context("Hero")

    # Verify
    assert context["entity"] == "Hero"
    # assert context["type"] == "Concept" # Default type

    # Check Outgoing
    outgoing = [r for r in context["outgoing_relations"] if r["to"] == "Villain"]
    assert len(outgoing) == 1
    assert outgoing[0]["relation"] == "attacks"

    # Check Incoming
    incoming = [r for r in context["incoming_relations"] if r["from"] == "Villager"]
    assert len(incoming) == 1
    assert incoming[0]["relation"] == "praises"

    # Check Attributes
    attributes = [a for a in context["attributes"] if a["attribute"] == "Brave"]
    assert len(attributes) == 1
    assert attributes[0]["type"] == "has_attribute"

@pytest.mark.asyncio
async def test_get_entity_context_query_count(graph_manager):
    gm = graph_manager
    await gm.add_triple("Hero", "attacks", "Villain")
    await gm.add_triple("Villager", "praises", "Hero")
    await gm.add_triple("Hero", "has_attribute", "Brave")

    # Reset query counter
    query_count = 0

    def before_cursor_execute(conn, cursor, statement, parameters, context, executemany):
        nonlocal query_count
        # Filter out transaction related queries if any (SAVEPOINT, RELEASE, etc)
        if "SELECT" in str(statement).upper():
             query_count += 1

    # Attach listener to the sync engine
    event.listen(gm.engine.sync_engine, "before_cursor_execute", before_cursor_execute)

    # Execute
    await gm.get_entity_context("Hero")

    # Detach listener (cleanup)
    event.remove(gm.engine.sync_engine, "before_cursor_execute", before_cursor_execute)

    # Expected:
    # Current implementation does:
    # 1. Select Entity (ID, type, metadata)
    # 2. Select Incoming
    # 3. Select Outgoing
    # 4. Select Attributes
    # Total = 4

    print(f"Query Count: {query_count}")

    # Verify optimization: Should be at most 2 queries (1 for entity, 1 for relations)
    # Original implementation was 4 queries.
    assert query_count <= 2
    assert query_count > 0
