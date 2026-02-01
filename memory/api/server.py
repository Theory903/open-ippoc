import os
from fastapi import FastAPI, HTTPException, Body
from pydantic import BaseModel
from typing import List, Optional, Dict, Any
from dotenv import load_dotenv
from ..semantic.rag import SemanticManager
from ..episodic.manager import EpisodicManager
from ..logic.consolidator import MemoryConsolidator
from ..graph.manager import GraphManager
from ..procedural.manager import ProceduralManager

# Load environment variables
load_dotenv()

app = FastAPI(
    title="IPPOC Memory Service",
    description="Unified Episodic & Semantic Memory API for OpenClaw interaction",
    version="0.1.0"
)

# Initialize Managers
semantic = SemanticManager()
episodic = EpisodicManager()
consolidator = MemoryConsolidator(episodic, semantic)
graph = GraphManager()
procedural = ProceduralManager(semantic)

@app.on_event("startup")
async def startup():
    print("Initializing DBs...")
    await episodic.init_db()
    await graph.init_db()


# --- Data Models ---
class ObservationPacket(BaseModel):
    content: str
    metadata: Dict[str, Any] = {}
    source: str = "openclaw"
    modality: str = "text"

class SearchQuery(BaseModel):
    query: str
    limit: int = 5
    min_score: float = 0.7
    filter: Optional[Dict[str, Any]] = None

class SearchResult(BaseModel):
    content: str
    score: float
    metadata: Dict[str, Any]
    type: str  # "episodic" or "semantic"

# --- Endpoints ---

@app.get("/health")
async def health_check():
    return {"status": "active", "organ": "memory"}

@app.post("/v1/memory/search", response_model=List[SearchResult])
async def search_memory(query: SearchQuery):
    """
    Hybrid search: Queries both Episodic (Time) and Semantic (Knowledge) stores.
    """
    results = []
    
    # 1. Semantic Search (HiDB/PGVector)
    try:
        sem_results = await semantic.search(query.query, limit=query.limit)
        results.extend([SearchResult(**r) for r in sem_results])
    except Exception as e:
        print(f"Semantic Search Error: {e}")
    
    # 2. Episodic Search (Recent logs/Keywords)
    try:
        epi_results = await episodic.search(query.query, limit=query.limit)
        results.extend([SearchResult(**r) for r in epi_results])
    except Exception as e:
        print(f"Episodic Search Error: {e}")
    
    return results

@app.post("/v1/memory/observe")
async def observe(packet: ObservationPacket):
    """
    Ingest a new observation. Routes to appropriate storage layers.
    """
    # 1. Store in Episodic Log (Postgres)
    eid = await episodic.write(
        content=packet.content,
        source=packet.source,
        modality=packet.modality,
        metadata=packet.metadata
    )
    
    # 2. Always Embed for now (Plasticity logic to be added)
    await semantic.index(packet.content, packet.metadata)
    
    return {"status": "ingested", "id": str(eid)}

@app.post("/v1/memory/reflect")
async def reflect():
    """
    Triggers the Self-Improvement loop.
    Consolidates recent episodes into long-term semantic knowledge.
    """
    summary = await consolidator.consolidate_recent()
    return {"status": "completed", "summary": summary}

@app.post("/v1/memory/graph/add")
async def add_knowledge(source: str, relation: str, target: str):
    """
    Explicitly add a relationship to the Knowledge Graph.
    """
    res = await graph.add_triple(source, relation, target)
    return {"status": res}

@app.get("/v1/memory/graph/context")
async def get_graph_context(entity: str):
    """
    Get 1-hop neighbors from the Knowledge Graph.
    """
    neighbors = await graph.get_neighbors(entity)
    return {"entity": entity, "context": neighbors}

@app.post("/v1/memory/procedural/register")
async def register_skill(name: str, code: str, description: str):
    """
    Teach the agent a new skill (code snippet).
    """
    res = await procedural.register_skill(name, code, description)
    return {"status": res}

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)
