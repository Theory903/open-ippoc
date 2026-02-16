from fastapi import FastAPI, Depends, HTTPException, Security
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from pydantic import BaseModel
from typing import Dict, Optional
import uuid
import os
from pathlib import Path

app = FastAPI(title="Soma - Identity & Trust Service")

# Security
security = HTTPBearer()

# In-memory storage for demo purposes (replace with database in production)
registered_nodes: Dict[str, str] = {}  # node_id -> public_key
api_keys: Dict[str, str] = {}  # api_key -> node_id
memories: list = []  # Simple memory storage

class RegisterNodeRequest(BaseModel):
    node_id: str
    public_key: str

class TokenRequest(BaseModel):
    node_id: str
    scopes: Optional[list[str]] = None

@app.get("/health")
def health():
    return {"status": "soma_alive"}

@app.get("/v1/system/diagnostics")
def diagnostics():
    return {
        "status": "healthy",
        "identity": "ippoc-local",
        "trust": "active"
    }

@app.post("/v1/identity/register")
def register_node(request: RegisterNodeRequest):
    registered_nodes[request.node_id] = request.public_key
    return {"status": "success", "message": "Peer registered"}

@app.get("/v1/identity/trust/{node_id}")
def get_trust_level(node_id: str):
    if node_id not in registered_nodes:
        raise HTTPException(status_code=404, detail="Node not found")
    return {"node_id": node_id, "trust_level": "Trusted"}

@app.post("/v1/vault/tokens")
def get_tokens(request: TokenRequest):
    if request.node_id not in registered_nodes:
        raise HTTPException(status_code=403, detail="Insufficient trust")
    return {"status": "success", "tokens": {}}

@app.post("/v1/auth/issue")
def issue_api_key(node_id: str = "ippoc-local"):
    api_key = str(uuid.uuid4())
    api_keys[api_key] = node_id
    return {"status": "success", "api_key": api_key, "node_id": node_id}

@app.get("/v1/auth/verify")
def verify_api_key(credentials: HTTPAuthorizationCredentials = Security(security)):
    api_key = credentials.credentials
    if api_key not in api_keys:
        raise HTTPException(status_code=401, detail="Invalid API key")
    return {"status": "valid", "node_id": api_keys[api_key]}

@app.get("/v1/memory/recent")
def get_recent_memories(limit: int = 20):
    """Get recent memories with optional limit"""
    # Return the most recent memories (last 'limit' items)
    recent = memories[-limit:] if len(memories) > limit else memories
    return {"results": recent}

if __name__ == "__main__":
    import uvicorn
    port = int(os.getenv("IPPOC_SOMA_PORT", 8081))
    uvicorn.run(app, host="0.0.0.0", port=port)
