from langgraph.graph import StateGraph, END
from langchain_core.runnables import Runnable
from langchain_core.embeddings import Embeddings
from langchain_core.vectorstores import VectorStore

from mnemosyne.logic.state import MemoryState
from mnemosyne.logic.nodes.fetch_events import fetch_events
from mnemosyne.logic.nodes.extract_facts import extract_facts
from mnemosyne.logic.nodes.index_vectors import index_vectors
from mnemosyne.logic.nodes.update_procedural import update_procedural
from mnemosyne.logic.nodes.decay_prune import decay_prune

def build_memory_graph(llm: Runnable, vector_store: VectorStore, embeddings: Embeddings):
    """
    Constructs the compiled StateGraph for the Memory Service.
    
    Args:
        llm: ReAct-capable LLM for extraction and inference.
        vector_store: Vector Store implementation (e.g., PGVector).
        embeddings: Embedding model.
    """
    graph = StateGraph(MemoryState)

    # 1. Add Nodes
    graph.add_node("fetch_events", fetch_events)
    graph.add_node("extract_facts", extract_facts(llm))
    graph.add_node("index_vectors", index_vectors(vector_store, embeddings))
    graph.add_node("update_procedural", update_procedural(llm))
    graph.add_node("decay_prune", decay_prune)

    # 2. Set Entry Point
    graph.set_entry_point("fetch_events")

    # 3. Add Edges (Linear flow for now, can become cyclic later)
    graph.add_edge("fetch_events", "extract_facts")
    graph.add_edge("extract_facts", "index_vectors")
    graph.add_edge("index_vectors", "update_procedural")
    graph.add_edge("update_procedural", "decay_prune")
    graph.add_edge("decay_prune", END)

    # 4. Compile
    return graph.compile()
