import uvicorn
import sys
import os
from dotenv import load_dotenv
load_dotenv()
import time
import json
import uuid
import asyncio
import tempfile
import secrets
from fastapi import FastAPI, HTTPException, Depends, Security, Request
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from fastapi.responses import JSONResponse, PlainTextResponse, StreamingResponse
from typing import List, Optional, Dict, Any, Literal
from contextlib import asynccontextmanager
from ippoc.cortex.cortex.schemas import Signal, ActionCandidate, TelepathyMessage, ChatRoom
from ippoc.cortex.cortex.two_tower import TwoTowerEngine
from ippoc.cortex.cortex.telepathy import TelepathySwarm, TransportLayer, HttpTransport, MeshTransport
from ippoc.cortex.cortex.langgraph_engine import LangGraphEngine    
from ippoc.cortex.core.bootstrap import bootstrap_tools
from ippoc.cortex.core.orchestrator import get_orchestrator
from ippoc.cortex.core.tools.base import ToolInvocationEnvelope, ToolResult
from ippoc.cortex.core.exceptions import ToolExecutionError, BudgetExceeded, SecurityViolation
from ippoc.cortex.core.ledger import get_ledger, ExecutionStatus
from ippoc.cortex.core.redis_queue import get_queue
from ippoc.cortex.core.autonomy import run_autonomy_loop
from ippoc.cortex.cortex.persistence import ChatPersistence
from ippoc.maksad.intent_engine import get_intent_engine, IntentStatus
from ippoc.maksad.reflection_engine import get_reflection_engine
from ippoc.maksad.cognitive_bus import get_thought_queue, emit_thought
from ippoc.cortex.maintainer.sensors import run_sensor_loop
import nest_asyncio
nest_asyncio.apply()

try:
    from prometheus_client import Counter, Histogram, generate_latest, CONTENT_TYPE_LATEST
except Exception:  # pragma: no cover
    Counter = Histogram = None
    generate_latest = None
    CONTENT_TYPE_LATEST = "text/plain"

try:
    from opentelemetry import trace  # type: ignore
    from opentelemetry.sdk.resources import Resource  # type: ignore
    from opentelemetry.sdk.trace import TracerProvider  # type: ignore
    from opentelemetry.sdk.trace.export import BatchSpanProcessor  # type: ignore
    from opentelemetry.exporter.otlp.proto.http.trace_exporter import OTLPSpanExporter  # type: ignore
except Exception:  # pragma: no cover
    trace = None
    TracerProvider = None
    BatchSpanProcessor = None
    OTLPSpanExporter = None

# --- Configuration ---
# --- Configuration ---
# --- Security & Ports ---
from ippoc.runtime.ports import PORTS, get_port
from ippoc.runtime.bootstrap.auth import get_api_key
import socket
import requests

# Security: Use centralized key logic
IPPOC_API_KEY = get_api_key()
AUTH_ENABLED = os.getenv("IPPOC_AUTH_ENABLED", "true").lower() == "true"
SOMA_URL = os.getenv("IPPOC_SOMA_URL", "http://localhost:8081")
if not AUTH_ENABLED:
    print("⚠️  [Server] Auth disabled - running in unrestricted mode")

# Configuration
NODE_ID = os.getenv("NODE_ID", "ippoc-local")
PERSISTENCE_PATH = os.getenv("CHAT_DB_PATH", os.path.join(tempfile.gettempdir(), "ippoc_chat.json"))
PEER_NODES = [p for p in os.getenv("PEER_NODES", "").split(",") if p]

# Metrics Setup
if Counter and Histogram:
    ORCH_REQUESTS = Counter("ippoc_orchestrator_requests_total", "Orchestrator requests", ["tool", "status"])
    ORCH_LATENCY = Histogram("ippoc_orchestrator_latency_seconds", "Orchestrator latency", ["tool"])
else:  # pragma: no cover
    ORCH_REQUESTS = ORCH_LATENCY = None

# Orchestrator runtime
ledger = get_ledger()
queue = get_queue() # This was missing fix!

# Auth Security (only enabled if configured)
security = HTTPBearer()
TOKEN_SCOPES: Dict[str, List[str]] = {}
scopes_raw = os.getenv("ORCHESTRATOR_TOKENS_JSON")
if scopes_raw:
    try:
        TOKEN_SCOPES = json.loads(scopes_raw)
    except Exception:
        TOKEN_SCOPES = {}
# Enforce the active key has admin scope
if IPPOC_API_KEY:
    TOKEN_SCOPES.setdefault(IPPOC_API_KEY, ["*"])
    print(f"[DEBUG] IPPOC_API_KEY loaded: {IPPOC_API_KEY[:3]}... Length: {len(IPPOC_API_KEY)}")
print(f"[DEBUG] Valid tokens: {list(TOKEN_SCOPES.keys())}")

def validate_key_with_soma(token: str) -> bool:
    """
    Validate API key against Soma's verify endpoint.
    Returns True if valid, False otherwise.
    """
    try:
        response = requests.get(f"{SOMA_URL}/v1/auth/verify", headers={"Authorization": f"Bearer {token}"}, timeout=5)
        return response.status_code == 200
    except Exception:
        return False

def verify_api_key(request: Request, credentials: Optional[HTTPAuthorizationCredentials] = Security(security, scopes=[])):
    """
    Enforces Bearer Token Authentication.
    Validates against Soma for dynamic key verification.
    """
    if not AUTH_ENABLED:
        request.state.scopes = ["*"]
        request.state.token = "unauthenticated"
        return "unauthenticated"
        
    if not credentials:
        raise HTTPException(status_code=401, detail="Missing authentication")
        
    token = credentials.credentials
    
    # Check local cache first
    if token in TOKEN_SCOPES:
        request.state.scopes = TOKEN_SCOPES.get(token, [])
        request.state.token = token
        return token
    
    # Validate against Soma dynamically
    if validate_key_with_soma(token):
        # Cache valid token
        TOKEN_SCOPES[token] = ["*"]
        request.state.scopes = ["*"]
        request.state.token = token
        print(f"[Auth] Dynamically validated and cached token: {token[:8]}...")
        return token
    
    raise HTTPException(status_code=403, detail="Invalid API Key")

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

# --- Global Component Registry ---
# Used for runtime control by CLI/Admin
class SystemState:
    def __init__(self):
        self.autonomy_task: Optional[asyncio.Task] = None
        self.chronos_task: Optional[asyncio.Task] = None
        self.reflection_task: Optional[asyncio.Task] = None
        self.worker_task: Optional[asyncio.Task] = None
        self.sensor_task: Optional[asyncio.Task] = None
        self.autonomy_enabled: bool = os.getenv("IPPOC_AUTONOMY", "false").lower() == "true"
        self.autonomy_interval: int = int(os.getenv("IPPOC_HEARTBEAT_SECONDS", "60"))

system_state = SystemState()

# --- Lifespan ---
@asynccontextmanager
async def lifespan(app: FastAPI):
    # Startup
    print(f"[Server] Booting Node: {NODE_ID}")
    bootstrap_tools()
    
    # Emit boot thought
    await emit_thought("info", f"Cognitive Core Online: {NODE_ID}", {"version": "0.9.0-sovereign"})

    try:
        await ledger.init()
    except Exception as e:
        print(f"[Server] Ledger init failed: {e}")

    worker_task = None
    autonomy_task = None
    chronos_task = None
    reflection_task = None

    if queue and os.getenv("ORCHESTRATOR_WORKER", "false").lower() == "true":
        print("[Server] Starting orchestrator worker...")
        system_state.worker_task = asyncio.create_task(queue.consume(_queue_handler))
    
    if system_state.autonomy_enabled:
        print(f"[Server] Starting autonomy loop (every {system_state.autonomy_interval}s)...")
        system_state.autonomy_task = asyncio.create_task(run_autonomy_loop(system_state.autonomy_interval))
        print("[Server] Starting internal sensor loop...")
        sensor_interval = int(os.getenv("IPPOC_SENSOR_INTERVAL", "60"))
        system_state.sensor_task = asyncio.create_task(run_sensor_loop(sensor_interval))
    
    # Start Chronos & Reflection
    intent_interval = int(os.getenv("IPPOC_INTENT_TICK_SECONDS", "30"))
    reflect_interval = int(os.getenv("IPPOC_REFLECTION_SECONDS", "300"))
    
    system_state.chronos_task = asyncio.create_task(get_intent_engine().main_loop(intent_interval))
    system_state.reflection_task = asyncio.create_task(get_reflection_engine().main_loop(reflect_interval))

    # Load State
    global chat_rooms
    chat_rooms.update(chat_persistence.load())
    
    yield
    
    # Shutdown
    print("[Server] Shutting down...")
    chat_persistence.save(chat_rooms)
    if system_state.worker_task:
        system_state.worker_task.cancel()
    if system_state.autonomy_task:
        system_state.autonomy_task.cancel()
    if system_state.sensor_task:
        system_state.sensor_task.cancel()
    if system_state.chronos_task:
        system_state.chronos_task.cancel()
    if system_state.reflection_task:
        system_state.reflection_task.cancel()
    # Close HTTP clients if any
    for t in swarm.transports:
        if isinstance(t, HttpTransport):
             await t.client.aclose()

app = FastAPI(
    title="IPPOC Cognitive Core (Two-Tower + Chat)", 
    version="0.9.0-sovereign", # Unified Release Version
    lifespan=lifespan
)

# Request ID middleware
@app.middleware("http")
async def add_request_id(request: Request, call_next):
    req_id = request.headers.get("x-request-id") or str(uuid.uuid4())
    response = await call_next(request)
    response.headers["x-request-id"] = req_id
    return response

# --- Orchestrator Helpers ---

def _record_metrics(tool_name: str, status: str, duration: float) -> None:
    if ORCH_REQUESTS:
        ORCH_REQUESTS.labels(tool=tool_name, status=status).inc()
    if ORCH_LATENCY:
        ORCH_LATENCY.labels(tool=tool_name).observe(duration)


def _tool_error_response(code: str, message: str, retryable: bool = False, details: Any = None) -> ToolResult:
    return ToolResult(
        success=False,
        output=None,
        cost_spent=0.0,
        memory_written=False,
        warnings=[],
        error_code=code,
        message=message,
        retryable=retryable,
        details=details,
    )


def _require_tls(request: Request) -> None:
    if os.getenv("ORCHESTRATOR_REQUIRE_TLS", "false").lower() != "true":
        return
    proto = request.headers.get("x-forwarded-proto") or request.url.scheme
    if proto != "https":
        raise HTTPException(status_code=400, detail="TLS required")


def _authorize_scopes(scopes: List[str], envelope: ToolInvocationEnvelope) -> None:
    if "*" in scopes:
        return
    domain = envelope.domain
    action = envelope.action
    required = [
        f"{domain}:*",
        f"{domain}:{action}",
        "orchestrator:admin",
    ]
    if not any(scope in scopes for scope in required):
        raise HTTPException(status_code=403, detail="Insufficient scope")


def _authorize_simple(scopes: List[str], required: str) -> None:
    if "*" in scopes or required in scopes or "orchestrator:admin" in scopes:
        return
    raise HTTPException(status_code=403, detail="Insufficient scope")


def _normalize_envelope(request: Request, envelope: ToolInvocationEnvelope) -> ToolInvocationEnvelope:
    if not envelope.request_id:
        envelope.request_id = request.headers.get("x-request-id") or str(uuid.uuid4())
    if not envelope.trace_id:
        envelope.trace_id = request.headers.get("x-trace-id") or envelope.request_id
    if not envelope.caller:
        envelope.caller = request.headers.get("x-caller") or "api"
    if not envelope.tenant:
        envelope.tenant = request.headers.get("x-tenant")
    if not envelope.source:
        envelope.source = "api"
    return envelope


async def _execute_envelope(envelope: ToolInvocationEnvelope) -> ToolResult:
    orc = get_orchestrator()
    start = time.monotonic()
    tool_name = envelope.tool_name
    try:
        result = await orc.invoke_async(envelope)
        _record_metrics(tool_name, "success", time.monotonic() - start)
        return result
    except BudgetExceeded as e:
        _record_metrics(tool_name, "budget_exceeded", time.monotonic() - start)
        return _tool_error_response("budget_exceeded", str(e), retryable=False)
    except SecurityViolation as e:
        _record_metrics(tool_name, "security_violation", time.monotonic() - start)
        return _tool_error_response("security_violation", str(e), retryable=False)
    except ToolExecutionError as e:
        _record_metrics(tool_name, "tool_error", time.monotonic() - start)
        return _tool_error_response("tool_error", str(e), retryable=True)
    except Exception as e:
        _record_metrics(tool_name, "internal_error", time.monotonic() - start)
        return _tool_error_response("internal_error", str(e), retryable=True)


async def _execute_with_ledger(envelope: ToolInvocationEnvelope) -> ToolResult:
    execution_id = envelope.request_id or str(uuid.uuid4())
    idempotency_key = envelope.idempotency_key

    if idempotency_key:
        existing = await ledger.get_by_idempotency(idempotency_key)
        if existing and existing.get("result"):
            return ToolResult(**existing["result"])

    try:
        await ledger.create(
            {
                "execution_id": execution_id,
                "status": ExecutionStatus.running.value,
                "tool_name": envelope.tool_name,
                "domain": envelope.domain,
                "action": envelope.action,
                "request_id": envelope.request_id,
                "idempotency_key": envelope.idempotency_key,
                "trace_id": envelope.trace_id,
                "caller": envelope.caller,
                "tenant": envelope.tenant,
                "source": envelope.source,
                "priority": envelope.priority,
            }
        )
    except Exception as e:
        print(f"[Server] Ledger create failed: {e}")

    started = time.monotonic()
    result = await _execute_envelope(envelope)
    duration_ms = int((time.monotonic() - started) * 1000)

    try:
        await ledger.update(
            execution_id,
            status=ExecutionStatus.completed.value if result.success else ExecutionStatus.failed.value,
            duration_ms=duration_ms,
            cost_spent=result.cost_spent or 0.0,
            result=result.model_dump() if hasattr(result, "model_dump") else result.dict(),
            error_code=result.error_code,
            error_message=result.message,
        )
    except Exception as e:
        print(f"[Server] Ledger update failed: {e}")
    return result


async def _queue_handler(execution_id: str, envelope_payload: Dict[str, Any]) -> None:
    record = await ledger.get(execution_id)
    if record and record.get("status") == ExecutionStatus.cancelled.value:
        return
    envelope = ToolInvocationEnvelope(**envelope_payload)
    started = time.monotonic()
    result = await _execute_envelope(envelope)
    duration_ms = int((time.monotonic() - started) * 1000)
    await ledger.update(
        execution_id,
        status=ExecutionStatus.completed.value if result.success else ExecutionStatus.failed.value,
        duration_ms=duration_ms,
        cost_spent=result.cost_spent or 0.0,
        result=result.model_dump() if hasattr(result, "model_dump") else result.dict(),
        error_code=result.error_code,
        error_message=result.message,
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
async def execute_tool(envelope: ToolInvocationEnvelope, request: Request):
    _require_tls(request)
    scopes = getattr(request.state, "scopes", [])
    _authorize_scopes(scopes, envelope)
    envelope = _normalize_envelope(request, envelope)
    """
    Universal Gateway for Tool Execution.
    OpenClaw (or any plugin) sends a ToolInvocationEnvelope here.
    The Brain's Orchestrator handles permission, budget, and routing.
    """
    result = await _execute_with_ledger(envelope)
    if result.success:
        return result
    status = 500
    if result.error_code == "budget_exceeded":
        status = 402
    elif result.error_code == "security_violation":
        status = 403
    elif result.error_code == "tool_error":
        status = 400
    return JSONResponse(status_code=status, content=result.model_dump() if hasattr(result, "model_dump") else result.dict())


@app.post("/v1/orchestrator/execute", response_model=ToolResult, dependencies=[Depends(verify_api_key)])
async def orchestrator_execute(envelope: ToolInvocationEnvelope, request: Request):
    _require_tls(request)
    scopes = getattr(request.state, "scopes", [])
    _authorize_scopes(scopes, envelope)
    envelope = _normalize_envelope(request, envelope)
    result = await _execute_with_ledger(envelope)
    if result.success:
        return result
    status = 500
    if result.error_code == "budget_exceeded":
        status = 402
    elif result.error_code == "security_violation":
        status = 403
    elif result.error_code == "tool_error":
        status = 400
    return JSONResponse(status_code=status, content=result.model_dump() if hasattr(result, "model_dump") else result.dict())


@app.post("/v1/orchestrator/execute:batch", dependencies=[Depends(verify_api_key)])
async def orchestrator_execute_batch(envelopes: List[ToolInvocationEnvelope], request: Request):
    _require_tls(request)
    scopes = getattr(request.state, "scopes", [])
    normalized: List[ToolInvocationEnvelope] = []
    for envelope in envelopes:
        _authorize_scopes(scopes, envelope)
        normalized.append(_normalize_envelope(request, envelope))
    tasks = [asyncio.create_task(_execute_with_ledger(envelope)) for envelope in normalized]
    raw_results = await asyncio.gather(*tasks, return_exceptions=True)
    results: List[Dict[str, Any]] = []
    for item in raw_results:
        if isinstance(item, Exception):
            result = _tool_error_response("internal_error", str(item), retryable=True)
        else:
            result = item
        results.append(result.model_dump() if hasattr(result, "model_dump") else result.dict())
    return {"results": results}


@app.post("/v1/orchestrator/execute:async", dependencies=[Depends(verify_api_key)])
async def orchestrator_execute_async(envelope: ToolInvocationEnvelope, request: Request):
    _require_tls(request)
    scopes = getattr(request.state, "scopes", [])
    _authorize_scopes(scopes, envelope)
    envelope = _normalize_envelope(request, envelope)
    if queue is None:
        raise HTTPException(status_code=503, detail="Async queue not configured")

    execution_id = envelope.request_id or str(uuid.uuid4())
    if envelope.idempotency_key:
        existing = await ledger.get_by_idempotency(envelope.idempotency_key)
        if existing:
            return {"execution_id": existing.get("execution_id"), "status": existing.get("status")}
    try:
        await ledger.create(
            {
                "execution_id": execution_id,
                "status": ExecutionStatus.queued.value,
                "tool_name": envelope.tool_name,
                "domain": envelope.domain,
                "action": envelope.action,
                "request_id": envelope.request_id,
                "idempotency_key": envelope.idempotency_key,
                "trace_id": envelope.trace_id,
                "caller": envelope.caller,
                "tenant": envelope.tenant,
                "source": envelope.source,
                "priority": envelope.priority,
            }
        )
    except Exception as e:
        print(f"[Server] Ledger create failed: {e}")
    await queue.enqueue(execution_id, envelope.model_dump() if hasattr(envelope, "model_dump") else envelope.dict())
    return {"execution_id": execution_id, "status": ExecutionStatus.queued.value}


@app.get("/v1/orchestrator/executions/{execution_id}", dependencies=[Depends(verify_api_key)])
async def orchestrator_execution_status(execution_id: str, request: Request):
    _require_tls(request)
    _authorize_simple(getattr(request.state, "scopes", []), "orchestrator:read")
    record = await ledger.get(execution_id)
    if not record:
        raise HTTPException(status_code=404, detail="Execution not found")
    return record


@app.post("/v1/orchestrator/executions/{execution_id}/cancel", dependencies=[Depends(verify_api_key)])
async def orchestrator_cancel(execution_id: str, request: Request):
    _require_tls(request)
    _authorize_simple(getattr(request.state, "scopes", []), "orchestrator:write")
    record = await ledger.get(execution_id)
    if not record:
        raise HTTPException(status_code=404, detail="Execution not found")
    if record.get("status") in [ExecutionStatus.completed.value, ExecutionStatus.failed.value]:
        return {"execution_id": execution_id, "status": record.get("status")}
    await ledger.update(execution_id, status=ExecutionStatus.cancelled.value)
    return {"execution_id": execution_id, "status": ExecutionStatus.cancelled.value}


@app.get("/v1/orchestrator/timeline", dependencies=[Depends(verify_api_key)])
async def orchestrator_timeline(request: Request, limit: int = 50):
    _require_tls(request)
    _authorize_simple(getattr(request.state, "scopes", []), "orchestrator:read")
    return {"executions": await ledger.list_recent(limit)}


@app.get("/v1/orchestrator/budget", dependencies=[Depends(verify_api_key)])
async def orchestrator_budget(request: Request):
    _require_tls(request)
    _authorize_simple(getattr(request.state, "scopes", []), "economy:read")
    return {"budget": get_orchestrator().get_budget()}


def _read_json_file(path: str) -> Any:
    with open(path, "r", encoding="utf-8") as f:
        return json.load(f)


@app.get("/v1/orchestrator/explain/latest", dependencies=[Depends(verify_api_key)])
async def orchestrator_explain_latest(request: Request):
    _require_tls(request)
    _authorize_simple(getattr(request.state, "scopes", []), "orchestrator:read")
    path = os.getenv("AUTONOMY_EXPLAIN_PATH", "data/explainability.json")
    if not os.path.exists(path):
        raise HTTPException(status_code=404, detail="No explainability data")

    return await asyncio.to_thread(_read_json_file, path)


@app.get("/v1/orchestrator/explain/{execution_id}", dependencies=[Depends(verify_api_key)])
async def orchestrator_explain_execution(execution_id: str, request: Request):
    _require_tls(request)
    _authorize_simple(getattr(request.state, "scopes", []), "orchestrator:read")
    record = await ledger.get(execution_id)
    if not record:
        raise HTTPException(status_code=404, detail="Execution not found")
    return record


@app.get("/healthz")
def healthz():
    return {"status": "ok"}


@app.get("/readyz")
async def readyz():
    """
    Readiness probe for the Organ Supervisor (OSC-01).
    """
    orc = get_orchestrator()
    return {
        "status": "ready",
        "node_id": NODE_ID,
        "tools_loaded": list(orc.tools.keys())
    }

@app.get("/v1/system/diagnostics", dependencies=[Depends(verify_api_key)])
async def system_diagnostics():
    """
    Deep metabolic diagnostics for Cortex.
    """
    orc = get_orchestrator()
    refl = get_reflection_engine()
    return {
        "status": "healthy",
        "node_id": NODE_ID,
        "organs": {
            "orchestrator": {"tools": len(orc.tools)},
            "reflection": {"last_cycle": refl.last_reflection_time},
            "intent_engine": {"active": len(await get_intent_engine().get_active_intents())}
        }
    }


# --- Neural Interface (Streaming API) ---


@app.get("/v1/cognitive/stream", dependencies=[Depends(verify_api_key)])
async def stream_cognitive_state(request: Request):
    """
    SSE stream of IPPOC's internal state (thoughts, intents, reflections).
    """
    async def event_generator():
        # First, send current state
        refl = get_reflection_engine()
        intents = await get_intent_engine().get_active_intents()
        yield {
            "event": "init",
            "data": json.dumps({
                "active_intents": [i.model_dump() for i in intents],
                "last_reflection": refl.last_reflection_time
            })
        }

        queue = get_thought_queue()
        while True:
            # Check for client disconnect
            if await request.is_disconnected():
                break

            try:
                # Wait for next thought event
                thought = await asyncio.wait_for(queue.get(), timeout=1.0)
                level = thought.get("level", "thought")
                # Map info level to standard 'thought' event for Neural Interface
                event_type = "thought" if level == "info" else level
                
                yield f"event: {event_type}\ndata: {json.dumps(thought)}\n\n"
            except asyncio.TimeoutError:
                # Keepalive
                yield ": ping\n\n"
            except Exception as e:
                yield f"event: error\ndata: {str(e)}\n\n"

    return StreamingResponse(event_generator(), media_type="text/event-stream")

# --- Intent API (Chronos) ---

@app.post("/v1/intents/create", dependencies=[Depends(verify_api_key)])
async def create_intent(goal: str, urgency: float = 0.5, ttl: int = 3600):
    """
    Create a new autonomous intent in the Chronos engine.
    """
    intent_id = await get_intent_engine().add_intent(goal, urgency, ttl)
    return {"status": "intent_created", "intent_id": intent_id}

@app.get("/v1/intents/list", dependencies=[Depends(verify_api_key)])
async def list_intents():
    """
    List all active and pending intents.
    """
    intents = await get_intent_engine().get_active_intents()
    return {"intents": [i.model_dump() for i in intents]}

@app.post("/v1/system/autonomy/control", dependencies=[Depends(verify_api_key)])
async def control_autonomy(action: Literal["on", "off", "pause"]):
    """
    Control the Autonomy Loop at runtime.
    """
    if action == "on":
        if not system_state.autonomy_task or system_state.autonomy_task.done():
            system_state.autonomy_enabled = True
            system_state.autonomy_task = asyncio.create_task(run_autonomy_loop(system_state.autonomy_interval))
            return {"status": "autonomy_started"}
        return {"status": "autonomy_already_running"}
    
    elif action == "off" or action == "pause":
        if system_state.autonomy_task and not system_state.autonomy_task.done():
            system_state.autonomy_task.cancel()
            system_state.autonomy_enabled = False
            return {"status": f"autonomy_{action}d"}
        return {"status": "autonomy_not_running"}

@app.get("/v1/system/violations", dependencies=[Depends(verify_api_key)])
async def get_violations(limit: int = 20):
    """
    Retrieve security and canon violations from ledger and explainability logs.
    """
    # 1. From Ledger (Security Violations)
    try:
        executions = await ledger.list_recent(limit * 2)
        security_violations = [
            e for e in executions if e.get("error_code") == "security_violation"
        ]
    except Exception as e:
        print(f"[Violations] Ledger error: {e}")
        security_violations = []
    
    # 2. From Explainability Logs (Canon Violations)
    path = os.getenv("AUTONOMY_EXPLAIN_PATH", "data/explainability.json")
    canon_violations = []
    if os.path.exists(path):
        try:
            with open(path, "r") as f:
                data = json.load(f)
                # Look for "rejected" decisions with "canon_violation"
                if data.get("decision", {}).get("action") == "reject" and "canon_violation" in data.get("decision", {}).get("reason", ""):
                    canon_violations.append(data)
        except Exception:
            pass
            
    return {
        "security_violations": security_violations[:limit],
        "canon_violations": canon_violations[:limit]
    }

@app.get("/metrics")
def metrics():
    if not generate_latest:
        raise HTTPException(status_code=503, detail="Prometheus client not available")
    return PlainTextResponse(generate_latest(), media_type=CONTENT_TYPE_LATEST)

@app.get("/health")
def health():
    # Check if Soma is available
    soma_available = False
    try:
        import requests
        response = requests.get("http://localhost:8081/v1/system/diagnostics", timeout=2)
        soma_available = response.status_code == 200
    except Exception:
        pass
    
    # Determine auth status and system mode
    auth_enabled = AUTH_ENABLED and soma_available
    mode = "FULL" if soma_available and auth_enabled else "BRAIN_ONLY"
    
    # Determine which tools to report based on capabilities
    tools = []
    core_tools = ["memory", "body", "evolution", "cerebellum", "simulation"]
    social_tools = ["social", "maintainer", "economy", "earnings"]
    
    tools.extend(core_tools)
    if soma_available:
        tools.extend(social_tools)
    tools.append("native_shell")
    
    return {
        "status": "cognitive_core_active",
        "node_id": NODE_ID,
        "auth_enabled": auth_enabled,
        "soma": "up" if soma_available else "down",
        "mode": mode,
        "rooms_loaded": len(chat_rooms),
        "architecture": "two_tower",
        "tower_a": two_tower.tower_a_model_name,
        "tower_b": two_tower.tower_b_model_name,
        "tools_loaded": tools
    }

if __name__ == "__main__":
    import argparse
    parser = argparse.ArgumentParser(description="IPPOC Cortex Server")
    parser.add_argument("--host", default="0.0.0.0", help="Host interface to bind to")
    parser.add_argument("--port", type=int, default=get_port("cortex"), help="Port to bind to")
    args, _ = parser.parse_known_args()
    
    def port_available(port):
        with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
            return s.connect_ex(("127.0.0.1", port)) != 0

    if not port_available(args.port):
        print(f"❌ [Fatal] Port {args.port} is already in use. Aborting startup.")
        sys.exit(48) # Standard exit code for address in use

    uvicorn.run(app, host=args.host, port=args.port, log_level="warning")
