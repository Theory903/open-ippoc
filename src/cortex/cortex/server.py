import uvicorn
import os
import time
import json
import uuid
import asyncio
import secrets
from fastapi import FastAPI, HTTPException, Depends, Security, Request
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from fastapi.responses import JSONResponse, PlainTextResponse
from typing import List, Optional, Dict, Any, Literal
from contextlib import asynccontextmanager

# Import new Cognitive Core
from cortex.cortex.schemas import Signal, ActionCandidate, TelepathyMessage, ChatRoom
from cortex.cortex.two_tower import TwoTowerEngine
from cortex.cortex.telepathy import TelepathySwarm, TransportLayer, HttpTransport, MeshTransport
from cortex.cortex.langgraph_engine import LangGraphEngine    
from cortex.core.bootstrap import bootstrap_tools
from cortex.core.orchestrator import get_orchestrator
from cortex.core.tools.base import ToolInvocationEnvelope, ToolResult
from cortex.core.exceptions import ToolExecutionError, BudgetExceeded, SecurityViolation
from cortex.core.ledger import get_ledger, ExecutionStatus
from cortex.core.queue import get_queue
from cortex.core.autonomy import run_autonomy_loop
from cortex.cortex.persistence import ChatPersistence
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
NODE_ID = os.getenv("NODE_ID", "ippoc-local")

# Security: Generate a random key if not provided (Critical Fix)
IPPOC_API_KEY = os.getenv("IPPOC_API_KEY")
if not IPPOC_API_KEY:
    IPPOC_API_KEY = secrets.token_hex(32)
    print(f"[Server] ⚠️  SECURITY WARNING: IPPOC_API_KEY not set! Generated temporary admin key: {IPPOC_API_KEY}")

PERSISTENCE_PATH = os.getenv("CHAT_DB_PATH", "data/state/chat_rooms.json")
PEER_NODES = os.getenv("PEER_NODES", "").split(",") # Comma separated URLs
PEER_NODES = [p for p in PEER_NODES if p] # Filter empty

# Optional OpenTelemetry
if trace and TracerProvider and OTLPSpanExporter:
    otel_endpoint = os.getenv("OTEL_EXPORTER_OTLP_ENDPOINT")
    if otel_endpoint:
        provider = TracerProvider(resource=Resource.create({"service.name": "ippoc-cortex"}))
        processor = BatchSpanProcessor(OTLPSpanExporter(endpoint=otel_endpoint))
        provider.add_span_processor(processor)
        trace.set_tracer_provider(provider)

# Orchestrator runtime
ledger = get_ledger()
queue = get_queue()

# Metrics
if Counter and Histogram:
    ORCH_REQUESTS = Counter("ippoc_orchestrator_requests_total", "Orchestrator requests", ["tool", "status"])
    ORCH_LATENCY = Histogram("ippoc_orchestrator_latency_seconds", "Orchestrator latency", ["tool"])
else:  # pragma: no cover
    ORCH_REQUESTS = ORCH_LATENCY = None

# --- Auth Security ---
security = HTTPBearer()

# Token scopes (token -> list of scopes). If not provided, fallback to IPPOC_API_KEY with admin scope.
TOKEN_SCOPES: Dict[str, List[str]] = {}
scopes_raw = os.getenv("ORCHESTRATOR_TOKENS_JSON")
if scopes_raw:
    try:
        TOKEN_SCOPES = json.loads(scopes_raw)
    except Exception:
        TOKEN_SCOPES = {}
if IPPOC_API_KEY:
    TOKEN_SCOPES.setdefault(IPPOC_API_KEY, ["*"])

def verify_api_key(request: Request, credentials: HTTPAuthorizationCredentials = Security(security)):
    """
    Enforces Bearer Token Authentication.
    """
    token = credentials.credentials
    if token not in TOKEN_SCOPES:
        raise HTTPException(status_code=403, detail="Invalid API Key")
    request.state.scopes = TOKEN_SCOPES.get(token, [])
    request.state.token = token
    return token

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
    try:
        await ledger.init()
    except Exception as e:
        print(f"[Server] Ledger init failed: {e}")

    worker_task = None
    autonomy_task = None
    if queue and os.getenv("ORCHESTRATOR_WORKER", "false").lower() == "true":
        print("[Server] Starting orchestrator worker...")
        worker_task = asyncio.create_task(queue.consume(_queue_handler))
    if os.getenv("IPPOC_AUTONOMY", "false").lower() == "true":
        interval = int(os.getenv("IPPOC_HEARTBEAT_SECONDS", "60"))
        print(f"[Server] Starting autonomy loop (every {interval}s)...")
        autonomy_task = asyncio.create_task(run_autonomy_loop(interval))
    
    # Load State
    global chat_rooms
    chat_rooms.update(chat_persistence.load())
    
    yield
    
    # Shutdown
    print("[Server] Shutting down...")
    chat_persistence.save(chat_rooms)
    if worker_task:
        worker_task.cancel()
    if autonomy_task:
        autonomy_task.cancel()
    # Close HTTP clients if any
    for t in swarm.transports:
        if isinstance(t, HttpTransport):
             await t.client.aclose()

app = FastAPI(
    title="IPPOC Cognitive Core (Two-Tower + Chat)", 
    version="3.2.0-PROD",
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
    # Minimal readiness check: ledger init + orchestrator tools
    return {
        "status": "ready",
        "tools_loaded": list(get_orchestrator().tools.keys())
    }


@app.get("/metrics")
def metrics():
    if not generate_latest:
        raise HTTPException(status_code=503, detail="Prometheus client not available")
    return PlainTextResponse(generate_latest(), media_type=CONTENT_TYPE_LATEST)

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
