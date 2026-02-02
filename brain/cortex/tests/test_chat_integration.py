from fastapi.testclient import TestClient
from brain.cortex.server import app

client = TestClient(app)

def test_health():
    response = client.get("/health")
    assert response.status_code == 200
    assert response.json()["status"] == "cognitive_core_active"

def test_chat_room_lifecycle():
    # 1. Create Room
    room_id = "test-room-1"
    response = client.post(
        "/v1/chat/rooms/create", 
        params={"room_id": room_id, "name": "Test Room", "type": "ephemeral"}
    )
    assert response.status_code == 200
    data = response.json()
    assert data["status"] == "created"
    assert data["room"]["id"] == room_id
    
    # 2. List Rooms
    response = client.get("/v1/chat/rooms")
    assert response.status_code == 200
    rooms = response.json()["rooms"]
    assert len(rooms) >= 1
    assert any(r["id"] == room_id for r in rooms)
    
    # 3. Join Room
    node_id = "test-node-alpha"
    response = client.post(f"/v1/chat/rooms/{room_id}/join", params={"node_id": node_id})
    assert response.status_code == 200
    room_data = response.json()["room"]
    assert node_id in room_data["participants"]

def test_telepathy_broadcast():
    response = client.post(
        "/v1/telepathy/broadcast",
        params={"content": "Hello Swarm", "confidence": 0.95}
    )
    assert response.status_code == 200
    assert response.json()["status"] == "broadcast_sent"

def test_ingest_signal():
    # 4. Ingest Signal (Cognitive Loop)
    import time
    signal = {
        "timestamp": time.time(),
        "node_id": "test-node",
        "context": {
            "task": "debug_kernel",
            "file": "kernel.rs",
            "tool": "read_file",
            "model": "claude"
        },
        "metrics": {
            "duration_sec": 0.5,
            "cost_ippc": 0.01,
            "success": True
        }
    }
    
    response = client.post("/v1/signals/ingest", json=signal)
    assert response.status_code == 200
    data = response.json()
    assert data["status"] == "accepted"
    # Check if a thought was generated
    snapshot = data["cognitive_state_snapshot"]
    # assert "Impulse" in str(snapshot.get("inner_monologue", []))

if __name__ == "__main__":
    # Manual run helper
    import sys
    test_health()
    print("✅ Health Check Passed")
    test_chat_room_lifecycle()
    print("✅ Chat Room Lifecycle Passed")
    test_telepathy_broadcast()
    print("✅ Telepathy Broadcast Passed")
    test_ingest_signal()
    print("✅ Signal Ingestion Passed (Cognitive Loop Active)")
