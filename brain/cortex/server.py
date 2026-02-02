import uvicorn
import os
from fastapi import FastAPI, HTTPException, Depends, Security
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from typing import List, Optional, Dict, Any, Literal
from contextlib import asynccontextmanager

# Import new Cognitive Core
from brain.cortex.schemas import Signal, ActionCandidate, TelepathyMessage, ChatRoom
from brain.cortex.two_tower import TwoTowerEngine
from brain.cortex.telepathy import TelepathySwarm, TransportLayer, HttpTransport, MeshTransport
from brain.cortex.langgraph_engine import LangGraphEngine    
from brain.core.bootstrap import bootstrap_tools
from brain.core.orchestrator import get_orchestrator
from brain.core.tools.base import ToolInvocationEnvelope, ToolResult
from brain.core.exceptions import ToolExecutionError, BudgetExceeded
from brain.cortex.persistence import ChatPersistence
import nest_asyncio
nest_asyncio.apply()

# --- Configuration ---
NODE_ID = os.getenv("NODE_ID", "ippoc-local")
IPPOC_API_KEY = os.getenv("IPPOC_API_KEY", "ippoc-secret-key") # Default for dev, warn in prod
PERSISTENCE_PATH = os.getenv("CHAT_DB_PATH", "data/state/chat_rooms.json")
PEER_NODES = os.getenv("PEER_NODES", "").split(",") # Comma separated URLs
PEER_NODES = [p for p in PEER_NODES if p] # Filter empty

# --- Auth Security ---
security = HTTPBearer()

def verify_api_key(credentials: HTTPAuthorizationCredentials = Security(security)):
    """
    Enforces Bearer Token Authentication.
    """
    if credentials.credentials != IPPOC_API_KEY:
        raise HTTPException(status_code=403, detail="Invalid API Key")
    return credentials.credentials

# --- Dependencies Definition ---
class MockTransport(TransportLayer):
    async def send(self, message: TelepathyMessage, target_node_id: Optional[str] = None):
        print(f"[Transport] Sending: {message}")
    
    async def receive(self) -> TelepathyMessage:
        return TelepathyMessage(type="THOUGHT", sender="mock", content="ping")

# --- State & Persistence ---
chat_persistence = ChatPersistence(storage_path=PERSISTENCE_PATH)
chat_rooms: Dict[str, ChatRoom] = {}

# --- Initialization ---
# Use Real Transport if Peers are defined, else Mock
transports = []

# Always add MeshTransport (via TUI local bridge)
transports.append(MeshTransport())
print("[Server] IPPOC Telepathy Mesh Transport Initialized (via TUI Bridge).")

if PEER_NODES:
    transports.append(HttpTransport(peers=PEER_NODES))
    print(f"[Server] Configured P2P Mesh with {len(PEER_NODES)} peers.")
else:
    # If no mesh and no peers, use mock for the HTTP portion
    transports.append(MockTransport())
    print("[Server] No peers configured. Using MockTransport for WAN.")

swarm = TelepathySwarm(node_id=NODE_ID, transports=transports)
two_tower = TwoTowerEngine()
engine = LangGraphEngine(two_tower, swarm)

# --- Lifespan ---
@asynccontextmanager
async def lifespan(app: FastAPI):
    # Startup
    print(f"[Server] Booting Node: {NODE_ID}")
    bootstrap_tools()
    
    # Load State
    global chat_rooms
    chat_rooms.update(chat_persistence.load())
    
    yield
    
    # Shutdown
    print("[Server] Shutting down...")
    chat_persistence.save(chat_rooms)
    # Close HTTP clients if any
    for t in swarm.transports:
        if isinstance(t, HttpTransport):
             await t.client.aclose()

app = FastAPI(
    title="IPPOC Cognitive Core (Two-Tower + Chat)", 
    version="3.2.0-PROD",
    lifespan=lifespan
)

# --- Endpoints ---

@app.post("/v1/signals/ingest", dependencies=[Depends(verify_api_key)])
async def ingest_signal(signal: Signal):
    """
    Body (OpenClaw) sends perception signals here.
    """
    state_update = await engine.run_step(signal)
    return {"status": "accepted", "cognitive_state_snapshot": state_update}

@app.post("/v1/telepathy/receive") # Public or Auth? P2P usually needs Mutual TLS or Shared Secret. Using same key for now.
async def receive_thought(message: TelepathyMessage, token: str = Depends(verify_api_key)):
    """
    Receive a thought from another Node in the Mesh.
    """
    processed = await swarm.handle_incoming(message)
    return {"status": "received", "processed": bool(processed)}

@app.post("/v1/telepathy/broadcast", dependencies=[Depends(verify_api_key)])
async def broadcast_thought(content: str, confidence: float):
    """
    Manually trigger a telepathic broadcast.
    """
    await swarm.broadcast_thought(content, confidence)
    return {"status": "broadcast_sent"}

@app.post("/v1/chat/rooms/create", dependencies=[Depends(verify_api_key)])
async def create_room(room_id: str, name: str, type: Literal["ephemeral", "persistent", "private"] = "ephemeral"):
    """
    Create a new Cognitive Chat Room.
    """
    if room_id in chat_rooms:
        raise HTTPException(status_code=400, detail="Room already exists")
    
    room = ChatRoom(
        id=room_id,
        name=name or room_id,
        type=type,
        min_reputation=0.5
    )
    chat_rooms[room_id] = room
    # Immediate persist for safety
    chat_persistence.save(chat_rooms)
    return {"status": "created", "room": room}

@app.get("/v1/chat/rooms", dependencies=[Depends(verify_api_key)])
async def list_rooms():
    return {"rooms": list(chat_rooms.values())}

@app.post("/v1/chat/rooms/{room_id}/join", dependencies=[Depends(verify_api_key)])
async def join_room(room_id: str, node_id: str):
    if room_id not in chat_rooms:
         raise HTTPException(status_code=404, detail="Room not found")
    
    room = chat_rooms[room_id]
    if node_id not in room.participants:
        room.participants.append(node_id)
        chat_persistence.save(chat_rooms)
        
    return {"status": "joined", "room": room}

@app.post("/v1/admin/model_market/update", dependencies=[Depends(verify_api_key)])
async def update_model_market(model: str, cost: float):
    current = two_tower.model_market.get(model)
    if current:
        current.avg_cost = cost
        two_tower.update_model_market(current)
        return {"status": "updated", "model": current}
    raise HTTPException(status_code=404, detail="Model not found")

@app.post("/v1/tools/execute", response_model=ToolResult, dependencies=[Depends(verify_api_key)])
async def execute_tool(envelope: ToolInvocationEnvelope):
    """
    Universal Gateway for Tool Execution.
    OpenClaw (or any plugin) sends a ToolInvocationEnvelope here.
    The Brain's Orchestrator handles permission, budget, and routing.
    """
    orc = get_orchestrator()
    try:
        # The invoke method is currently sync but might be async-bridged internally.
        # Since this is FastAPI async handler, blocking here is suboptimal but acceptable for prototype.
        # Ideally, invoke should be async.
        result = orc.invoke(envelope)
        return result
    except BudgetExceeded as e:
        raise HTTPException(status_code=402, detail=f"Budget Exceeded: {str(e)}")
    except ToolExecutionError as e:
        raise HTTPException(status_code=400, detail=f"Tool Error: {str(e)}")
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Internal Orchestrator Error: {str(e)}")

@app.get("/health")
def health():
    return {
        "status": "cognitive_core_active", 
        "node_id": NODE_ID,
        "auth_enabled": True,
        "rooms_loaded": len(chat_rooms),
        "architecture": "two_tower",
        "tower_a": two_tower.tower_a_model_name,
        "tower_b": two_tower.tower_b_model_name,
        "tools_loaded": list(get_orchestrator().tools.keys())
    }

if __name__ == "__main__":
    uvicorn.run(app, host="0.0.0.0", port=8001)
