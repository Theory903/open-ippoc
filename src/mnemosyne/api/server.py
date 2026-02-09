from fastapi import FastAPI, HTTPException, BackgroundTasks
from pydantic import BaseModel, Field
from typing import List, Dict, Any, Optional
import time
import os
import asyncio

# Import the Graph Builder (Phase 1)
from mnemosyne.logic.graph import build_memory_graph
from mnemosyne.logic.state import MemoryState, MemoryEvent, ExtractedFact

# Import HiDB singleton from package
from mnemosyne import hidb
from mnemosyne.hidb import MemoryRecord

# Import LangChain components for the builder
from langchain_google_genai import ChatGoogleGenerativeAI, GoogleGenerativeAIEmbeddings
from langchain_community.vectorstores import PGVector

app = FastAPI(title="IPPOC Hippocampus", version="2.0.0")

# --- Dependency Injection ---
llm = ChatGoogleGenerativeAI(model="gemini-flash-latest", temperature=0)
embeddings = GoogleGenerativeAIEmbeddings(model="models/text-embedding-004")

# Initialize Vector Store (Legacy/Fallback)
try:
    vector_store = PGVector(
        connection_string=os.getenv("DATABASE_URL", "postgresql://ippoc:ippoc@localhost:5432/ippoc"),
        embedding_function=embeddings,
        collection_name="hippocampus_v2",
    )
except Exception as e:
    # Log but don't exit hard, as HiDB might be the primary
    print(f"Warning: PGVector init failed: {e}")
    vector_store = None

memory_graph = build_memory_graph(llm, vector_store, embeddings)

# --- API Models ---

class EventInput(BaseModel):
    content: str
    source: str = "unknown"
    confidence: float = 0.5
    metadata: Dict[str, Any] = {}

class SearchInput(BaseModel):
    query: Optional[str] = None
    vector: Optional[List[float]] = None
    limit: int = 5

class StoreInput(BaseModel):
    content: str
    vector: List[float]
    metadata: Optional[Dict[str, Any]] = {}

class MemoryResponse(BaseModel):
    status: str
    cycle_id: str
    facts_extracted: int

# --- Endpoints ---

@app.on_event("startup")
async def startup_event():
    await hidb.connect()

@app.on_event("shutdown")
async def shutdown_event():
    await hidb.close()

@app.post("/v1/memory/store")
async def store_memory(input_data: StoreInput):
    """
    Store memory directly into HiDB.
    """
    try:
        record = MemoryRecord(
            content=input_data.content,
            embedding=input_data.vector,
            metadata=input_data.metadata
        )
        record_id = await hidb.insert_memory(record)
        return {"id": record_id, "status": "stored"}
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/v1/memory/search")
async def search_memory(search: SearchInput):
    """
    Semantic search over the vector store (HiDB or PGVector).
    """
    try:
        if search.vector:
            # Direct vector search via HiDB
            results = await hidb.semantic_search(search.vector, k=search.limit)
            return [
                {
                    "id": r.id,
                    "content": r.content,
                    "metadata": r.metadata,
                    "score": r.score # Uses similarity score (1 - distance)
                }
                for r in results
            ]
        elif search.query and vector_store:
            # Text search via LangChain/PGVector
            results = await vector_store.asimilarity_search_with_score(search.query, k=search.limit)
            return [
                {"content": doc.page_content, "metadata": doc.metadata, "score": score}
                for doc, score in results
            ]
        else:
            raise HTTPException(status_code=400, detail="Either 'vector' (for HiDB) or 'query' (for Text Search) is required.")

    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/v1/memory/consolidate", response_model=MemoryResponse)
async def consolidate_memory(event: EventInput, background_tasks: BackgroundTasks):
    """
    Triggers a memory consolidation cycle.
    This accepts an episodic event and runs it through the Cognitive Graph.
    """
    
    # Create initial state
    input_state = MemoryState(
        new_events=[
            MemoryEvent(
                event_id=f"evt-{time.time()}",
                timestamp=time.time(),
                source=event.source,
                content=event.content,
                confidence=event.confidence,
                metadata=event.metadata
            )
        ]
    )

    # Run Graph with Timeout & Fallback
    try:
        # Use asyncio.wait_for to ensure the brain doesn't hang the gateway
        final_state = await asyncio.wait_for(memory_graph.ainvoke(input_state), timeout=15.0)
        
        facts_count = len(final_state.get("extracted_facts", []))
        
        return MemoryResponse(
            status="consolidated",
            cycle_id=str(final_state.get("cycle_started_at", time.time())),
            facts_extracted=facts_count
        )
    except Exception as e:
        print(f"[Memory] Consolidation failed or timed out: {e}")
        
        # --- SIMPLE FALLBACK ---
        # If extraction fails, at least store the raw content as a "Dumb Fact"
        try:
            # Create a simple fact from the raw content
            input_state.extracted_facts = [
                ExtractedFact(
                    fact=f"[Fallback Memory]: {event.content}",
                    embedding=None,
                    confidence=0.5,
                    source_event_id=input_state.new_events[0].event_id
                )
            ]
            # Use the node's function directly if possible or wrap it
            from mnemosyne.logic.nodes.index_vectors import index_vectors
            # Requires vector_store to be valid for fallback logic currently implemented in nodes
            if vector_store:
                fallback_node = index_vectors(vector_store, embeddings)
                await fallback_node(input_state)
            
            return MemoryResponse(
                status="fallback_stored",
                cycle_id="fallback",
                facts_extracted=1
            )
        except Exception as fallback_err:
             print(f"[Memory] Fallback failed: {fallback_err}")
             raise HTTPException(status_code=500, detail=f"Memory Critical Failure: {e}")

@app.get("/health")
def health():
    return {"status": "hippocampus_active", "mode": "graph_v1", "hidb": "connected" if hidb._connected else "disconnected"}

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)
