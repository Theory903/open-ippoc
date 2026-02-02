from __future__ import annotations

import enum
import json
import os
import time
import uuid
from dataclasses import dataclass, asdict
from typing import Any, Dict, Optional

from sqlalchemy import Column, String, Float, Integer, DateTime, Text, select, text as sql_text
from sqlalchemy.ext.asyncio import AsyncEngine, AsyncSession, create_async_engine
from sqlalchemy.orm import declarative_base, sessionmaker

Base = declarative_base()


class ExecutionStatus(str, enum.Enum):
    queued = "queued"
    running = "running"
    completed = "completed"
    failed = "failed"
    cancelled = "cancelled"


class ExecutionRecord(Base):
    __tablename__ = "orchestrator_executions"

    execution_id = Column(String, primary_key=True)
    status = Column(String, default=ExecutionStatus.queued.value)
    tool_name = Column(String, index=True)
    domain = Column(String, index=True)
    action = Column(String, index=True)
    request_id = Column(String, index=True, nullable=True)
    idempotency_key = Column(String, index=True, nullable=True)
    trace_id = Column(String, index=True, nullable=True)
    caller = Column(String, index=True, nullable=True)
    tenant = Column(String, index=True, nullable=True)
    source = Column(String, index=True, nullable=True)
    priority = Column(Integer, nullable=True)
    created_at = Column(DateTime, server_default=sql_text("CURRENT_TIMESTAMP"))
    updated_at = Column(DateTime, server_default=sql_text("CURRENT_TIMESTAMP"))
    duration_ms = Column(Integer, nullable=True)
    retries = Column(Integer, default=0)
    cost_spent = Column(Float, default=0.0)
    result_json = Column(Text, nullable=True)
    error_code = Column(String, nullable=True)
    error_message = Column(Text, nullable=True)


@dataclass
class InMemoryExecution:
    execution_id: str
    status: str
    tool_name: str
    domain: str
    action: str
    request_id: Optional[str] = None
    idempotency_key: Optional[str] = None
    trace_id: Optional[str] = None
    caller: Optional[str] = None
    tenant: Optional[str] = None
    source: Optional[str] = None
    priority: Optional[int] = None
    created_at: float = 0.0
    updated_at: float = 0.0
    duration_ms: Optional[int] = None
    retries: int = 0
    cost_spent: float = 0.0
    result: Optional[Dict[str, Any]] = None
    error_code: Optional[str] = None
    error_message: Optional[str] = None


class BaseLedger:
    async def init(self) -> None:
        return None

    async def create(self, payload: Dict[str, Any]) -> str:
        raise NotImplementedError

    async def update(self, execution_id: str, **fields: Any) -> None:
        raise NotImplementedError

    async def get(self, execution_id: str) -> Optional[Dict[str, Any]]:
        raise NotImplementedError

    async def get_by_idempotency(self, key: str) -> Optional[Dict[str, Any]]:
        raise NotImplementedError


class InMemoryLedger(BaseLedger):
    def __init__(self) -> None:
        self._data: Dict[str, InMemoryExecution] = {}

    async def create(self, payload: Dict[str, Any]) -> str:
        execution_id = payload.get("execution_id") or str(uuid.uuid4())
        now = time.time()
        record = InMemoryExecution(
            execution_id=execution_id,
            status=payload.get("status", ExecutionStatus.queued.value),
            tool_name=payload.get("tool_name", ""),
            domain=payload.get("domain", ""),
            action=payload.get("action", ""),
            request_id=payload.get("request_id"),
            idempotency_key=payload.get("idempotency_key"),
            trace_id=payload.get("trace_id"),
            caller=payload.get("caller"),
            tenant=payload.get("tenant"),
            source=payload.get("source"),
            priority=payload.get("priority"),
            created_at=now,
            updated_at=now,
        )
        self._data[execution_id] = record
        return execution_id

    async def update(self, execution_id: str, **fields: Any) -> None:
        record = self._data.get(execution_id)
        if not record:
            return None
        for key, value in fields.items():
            if hasattr(record, key):
                setattr(record, key, value)
        record.updated_at = time.time()

    async def get(self, execution_id: str) -> Optional[Dict[str, Any]]:
        record = self._data.get(execution_id)
        if not record:
            return None
        return asdict(record)

    async def get_by_idempotency(self, key: str) -> Optional[Dict[str, Any]]:
        for record in self._data.values():
            if record.idempotency_key == key:
                return asdict(record)
        return None


class SqlLedger(BaseLedger):
    def __init__(self, db_url: str) -> None:
        self.db_url = db_url
        self.engine: AsyncEngine = create_async_engine(db_url, echo=False)
        self.session_factory = sessionmaker(self.engine, expire_on_commit=False, class_=AsyncSession)

    async def init(self) -> None:
        async with self.engine.begin() as conn:
            await conn.run_sync(Base.metadata.create_all)

    async def create(self, payload: Dict[str, Any]) -> str:
        execution_id = payload.get("execution_id") or str(uuid.uuid4())
        async with self.session_factory() as session:
            record = ExecutionRecord(
                execution_id=execution_id,
                status=payload.get("status", ExecutionStatus.queued.value),
                tool_name=payload.get("tool_name", ""),
                domain=payload.get("domain", ""),
                action=payload.get("action", ""),
                request_id=payload.get("request_id"),
                idempotency_key=payload.get("idempotency_key"),
                trace_id=payload.get("trace_id"),
                caller=payload.get("caller"),
                tenant=payload.get("tenant"),
                source=payload.get("source"),
                priority=payload.get("priority"),
                duration_ms=payload.get("duration_ms"),
                retries=payload.get("retries", 0),
                cost_spent=payload.get("cost_spent", 0.0),
                result_json=json.dumps(payload.get("result") or {}),
                error_code=payload.get("error_code"),
                error_message=payload.get("error_message"),
            )
            session.add(record)
            await session.commit()
        return execution_id

    async def update(self, execution_id: str, **fields: Any) -> None:
        async with self.session_factory() as session:
            record = await session.get(ExecutionRecord, execution_id)
            if not record:
                return None
            for key, value in fields.items():
                if key == "result":
                    setattr(record, "result_json", json.dumps(value))
                elif hasattr(record, key):
                    setattr(record, key, value)
            setattr(record, "updated_at", sql_text("CURRENT_TIMESTAMP"))
            await session.commit()

    async def get(self, execution_id: str) -> Optional[Dict[str, Any]]:
        async with self.session_factory() as session:
            record = await session.get(ExecutionRecord, execution_id)
            if not record:
                return None
            return {
                "execution_id": record.execution_id,
                "status": record.status,
                "tool_name": record.tool_name,
                "domain": record.domain,
                "action": record.action,
                "request_id": record.request_id,
                "idempotency_key": record.idempotency_key,
                "trace_id": record.trace_id,
                "caller": record.caller,
                "tenant": record.tenant,
                "source": record.source,
                "priority": record.priority,
                "created_at": record.created_at.isoformat() if record.created_at else None,
                "updated_at": record.updated_at.isoformat() if record.updated_at else None,
                "duration_ms": record.duration_ms,
                "retries": record.retries,
                "cost_spent": record.cost_spent,
                "result": json.loads(record.result_json or "{}"),
                "error_code": record.error_code,
                "error_message": record.error_message,
            }

    async def get_by_idempotency(self, key: str) -> Optional[Dict[str, Any]]:
        async with self.session_factory() as session:
            stmt = select(ExecutionRecord).where(ExecutionRecord.idempotency_key == key)
            res = await session.execute(stmt)
            record = res.scalar_one_or_none()
            if not record:
                return None
            return {
                "execution_id": record.execution_id,
                "status": record.status,
                "tool_name": record.tool_name,
                "domain": record.domain,
                "action": record.action,
                "request_id": record.request_id,
                "idempotency_key": record.idempotency_key,
                "trace_id": record.trace_id,
                "caller": record.caller,
                "tenant": record.tenant,
                "source": record.source,
                "priority": record.priority,
                "created_at": record.created_at.isoformat() if record.created_at else None,
                "updated_at": record.updated_at.isoformat() if record.updated_at else None,
                "duration_ms": record.duration_ms,
                "retries": record.retries,
                "cost_spent": record.cost_spent,
                "result": json.loads(record.result_json or "{}"),
                "error_code": record.error_code,
                "error_message": record.error_message,
            }


_ledger_instance: Optional[BaseLedger] = None


def get_ledger() -> BaseLedger:
    global _ledger_instance
    if _ledger_instance is not None:
        return _ledger_instance

    ledger_enabled = os.getenv("ORCHESTRATOR_LEDGER_ENABLED", "true").lower() == "true"
    if not ledger_enabled:
        _ledger_instance = InMemoryLedger()
        return _ledger_instance

    db_url = os.getenv("ORCHESTRATOR_DB_URL") or os.getenv("EXECUTION_LEDGER_URL")
    if not db_url:
        db_url = "sqlite+aiosqlite:///data/orchestrator.db"

    _ledger_instance = SqlLedger(db_url)
    return _ledger_instance
