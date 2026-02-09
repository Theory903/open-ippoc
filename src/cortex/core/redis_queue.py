import asyncio
import json
import os
from typing import Any, Awaitable, Callable, Dict, Optional, Union

try:
    import redis.asyncio as redis
except Exception:  # pragma: no cover - optional dependency
    redis = None


class RedisQueue:
    def __init__(self, url: str, stream: str, group: str, consumer: str) -> None:
        if redis is None:
            raise RuntimeError("redis package not available")
        self.url = url
        self.stream = stream
        self.group = group
        self.consumer = consumer
        self.client = redis.from_url(url)

    async def ensure_group(self) -> None:
        try:
            await self.client.xgroup_create(self.stream, self.group, id="0", mkstream=True)
        except Exception:
            return None

    async def enqueue(self, execution_id: str, envelope: Dict[str, Any]) -> None:
        payload = {"execution_id": execution_id, "envelope": json.dumps(envelope)}
        await self.client.xadd(self.stream, payload)

    async def consume(self, handler: Callable[[str, Dict[str, Any]], Awaitable[None]]) -> None:
        await self.ensure_group()
        while True:
            results = await self.client.xreadgroup(
                groupname=self.group,
                consumername=self.consumer,
                streams={self.stream: ">"},
                count=10,
                block=5000,
            )
            if not results:
                continue
            for _stream, messages in results:
                for msg_id, fields in messages:
                    try:
                        execution_id = fields.get(b"execution_id", b"").decode()
                        envelope_json = fields.get(b"envelope", b"{}").decode()
                        envelope = json.loads(envelope_json)
                        await handler(execution_id, envelope)
                        await self.client.xack(self.stream, self.group, msg_id)
                    except Exception:
                        continue


class InternalQueue:
    def __init__(self) -> None:
        self.queue = asyncio.Queue()

    async def enqueue(self, execution_id: str, envelope: Dict[str, Any]) -> None:
        await self.queue.put((execution_id, envelope))

    async def consume(self, handler: Callable[[str, Dict[str, Any]], Awaitable[None]]) -> None:
        print("[InternalQueue] Starting task consumer...")
        while True:
            execution_id, envelope = await self.queue.get()
            try:
                await handler(execution_id, envelope)
            except Exception as e:
                print(f"[InternalQueue] Error handling {execution_id}: {e}")
            finally:
                self.queue.task_done()


_queue_instance: Union[RedisQueue, InternalQueue, None] = None


def get_queue() -> Union[RedisQueue, InternalQueue, None]:
    global _queue_instance
    if _queue_instance is not None:
        return _queue_instance

    use_internal = os.getenv("IPPOC_USE_INTERNAL_QUEUE", "false").lower() == "true"
    if use_internal:
        print("[Queue] Using isolated internal asyncio queue.")
        _queue_instance = InternalQueue()
        return _queue_instance

    url = os.getenv("ORCHESTRATOR_REDIS_URL") or os.getenv("REDIS_URL")
    if not url:
        return None

    stream = os.getenv("ORCHESTRATOR_QUEUE_STREAM", "ippoc:orchestrator:requests")
    group = os.getenv("ORCHESTRATOR_QUEUE_GROUP", "orchestrator-workers")
    consumer = os.getenv("ORCHESTRATOR_QUEUE_CONSUMER", "orchestrator-1")

    try:
        _queue_instance = RedisQueue(url, stream, group, consumer)
    except Exception:
        return None
    return _queue_instance
