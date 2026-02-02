from fastapi import FastAPI, HTTPException, BackgroundTasks
from pydantic import BaseModel, Field
from typing import List, Dict, Any, Optional
import time
import os

# Import the Graph Builder (Phase 1)
from memory.logic.graph import build_memory_graph
from memory.logic.state import MemoryState, MemoryEvent

# Import LangChain components for the builder
from langchain_google_genai import ChatGoogleGenerativeAI, GoogleGenerativeAIEmbeddings
from langchain_community.vectorstores import PGVector # legacy import wrapper or direct?
# We used valid imports in rag.py, let's reuse what works. 
# Ideally we inject dependencies.

app = FastAPI(title="IPPOC Hippocampus", version="2.0.0")

# --- Dependency Injection (Simple Global for now) ---
# In production, use lifespan events or dependency overrides
llm = ChatGoogleGenerativeAI(model="gemini-flash-latest", temperature=0) # Smart model for extraction
embeddings = GoogleGenerativeAIEmbeddings(model="models/text-embedding-004")
try:
    vector_store = PGVector(
        connection_string=os.getenv("DATABASE_URL", "postgresql://ippoc:ippoc@localhost:5432/ippoc"),
        embedding_function=embeddings,
        collection_name="hippocampus_v2",
    )
except Exception as e:
    if "could not open extension control file" in str(e) or "vector" in str(e):
        print("\n\033[91mCRITICAL ERROR: 'pgvector' extension missing from PostgreSQL.\033[0m")
        print("Please install it (e.g., 'brew install pgvector' or 'sudo apt install postgresql-14-pgvector').")
        print(f"Details: {e}\n")
        import sys; sys.exit(1)
    raise e

memory_graph = build_memory_graph(llm, vector_store, embeddings)

# --- API Models ---

class EventInput(BaseModel):
    content: str
    source: str = "unknown"
    confidence: float = 0.5
    metadata: Dict[str, Any] = {}

class SearchInput(BaseModel):
    query: str
    limit: int = 5

class MemoryResponse(BaseModel):
    status: str
    cycle_id: str
    facts_extracted: int

# --- Endpoints ---

@app.post("/v1/memory/search")
async def search_memory(search: SearchInput):
    """
    Semantic search over the vector store.
    """
    try:
        results = await vector_store.asimilarity_search_with_score(search.query, k=search.limit)
        return [
            {"content": doc.page_content, "metadata": doc.metadata, "score": score} 
            for doc, score in results
        ]
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

    # Run Graph
    # We await here for synchronous feedback, or use background tasks if slow.
    # For now, let's await to confirm it works.
    
    try:
        final_state = await memory_graph.ainvoke(input_state)
        # Type check: final_state might be a dict or object depending on langgraph version
        # StateGraph usually returns the state dictionary.
        
        facts_count = len(final_state.get("extracted_facts", []))
        
        return MemoryResponse(
            status="consolidated",
            cycle_id=str(final_state.get("cycle_started_at")),
            facts_extracted=facts_count
        )
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/health")
def health():
    return {"status": "hippocampus_active", "mode": "graph_v1"}

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)
