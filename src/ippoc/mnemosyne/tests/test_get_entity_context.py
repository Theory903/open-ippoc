
import pytest
import pytest_asyncio
import sys
import os
import asyncio

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
async def test_get_entity_context_bug(graph_manager):
    gm = graph_manager
    entity = "TestEntity"
    await gm.add_triple(entity, "is_a", "TestObject")

    # This should fail if metadata_ column is queried but doesn't exist
    context = await gm.get_entity_context(entity)

    assert "error" not in context, f"Got error: {context.get('error')}"
    assert context["entity"] == entity
    assert context["type"] == "TestObject"

@pytest.mark.asyncio
async def test_get_entity_context_relations(graph_manager):
    gm = graph_manager
    entity = "Center"
    await gm.add_triple(entity, "out_rel", "Target")
    await gm.add_triple("Source", "in_rel", entity)
    await gm.add_triple(entity, "has_attribute", "Attr")

    context = await gm.get_entity_context(entity)

    assert "error" not in context

    outgoing = [r["relation"] for r in context.get("outgoing_relations", [])]
    incoming = [r["relation"] for r in context.get("incoming_relations", [])]
    attributes = [a["attribute"] for a in context.get("attributes", [])]

    # Note: 'has_attribute' is also an outgoing relation
    assert "out_rel" in outgoing
    assert "has_attribute" in outgoing
    assert "in_rel" in incoming
    assert "Attr" in attributes
