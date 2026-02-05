"""
HiDB Client - Python Interface to the Cognitive Substrate
"""

import os
import json
import asyncio
import uuid
import time
import logging
from typing import List, Optional, Dict, Any, Union
from dataclasses import dataclass, asdict

# Configure logger
logger = logging.getLogger(__name__)

try:
    import asyncpg
    import pgvector.asyncpg
except ImportError:
    asyncpg = None

try:
    import redis.asyncio as redis
except ImportError:
    redis = None

@dataclass
class MemoryRecord:
    """Represents a memory record in HiDB"""
    content: str
    embedding: List[float]
    source: str = "node"
    confidence: float = 1.0
    decay_rate: float = 0.1
    id: Optional[str] = None
    created_at: Optional[Any] = None
    updated_at: Optional[Any] = None
    metadata: Optional[Dict[str, Any]] = None

    def to_dict(self) -> Dict[str, Any]:
        d = asdict(self)
        if d['created_at']:
            d['created_at'] = str(d['created_at'])
        if d['updated_at']:
            d['updated_at'] = str(d['updated_at'])
        return d

class HiDB:
    """
    The Cognitive Substrate (Vector Database).
    Abstracts PostgreSQL/pgvector and Redis into a single Memory interface.
    """
    def __init__(self, db_url: str = None, redis_url: str = None):
        """
        Initialize the HiDB client.

        Args:
            db_url: PostgreSQL connection string. Defaults to HIDB_DATABASE_URL or DATABASE_URL env var.
            redis_url: Redis connection string. Defaults to HIDB_REDIS_URL or REDIS_URL env var.
        """
        self.db_url = db_url or os.getenv("HIDB_DATABASE_URL") or os.getenv("DATABASE_URL")
        self.redis_url = redis_url or os.getenv("HIDB_REDIS_URL") or os.getenv("REDIS_URL")
        self.pool = None
        self.redis = None
        self._connected = False

    async def connect(self):
        """Establish connections to PostgreSQL and Redis"""
        if self._connected:
            return

        if not asyncpg:
            raise ImportError("asyncpg is required for HiDB. Please install it.")

        if self.db_url and not self.pool:
            async def init_connection(conn):
                await pgvector.asyncpg.register_vector(conn)

            try:
                self.pool = await asyncpg.create_pool(self.db_url, init=init_connection)
            except Exception as e:
                # Log error or handle gracefully if DB is not available yet
                logger.error(f"HiDB: Failed to connect to PostgreSQL: {e}")

        if self.redis_url and not self.redis:
            try:
                if redis:
                    self.redis = redis.from_url(self.redis_url)
                else:
                    logger.warning("HiDB: Redis client not installed (redis-py). Redis caching disabled.")
            except Exception as e:
                logger.error(f"HiDB: Failed to connect to Redis: {e}")

        self._connected = True

    async def close(self):
        """Close connections"""
        if self.pool:
            await self.pool.close()
            self.pool = None
        if self.redis:
            await self.redis.close()
            self.redis = None
        self._connected = False

    async def insert_memory(self, record: MemoryRecord) -> str:
        """
        Insert a memory record into HiDB.

        Args:
            record: MemoryRecord object

        Returns:
            The ID of the inserted record
        """
        if not self.pool:
            await self.connect()
            if not self.pool:
                raise RuntimeError("HiDB: Not connected to database")

        record.id = str(uuid.uuid4()) if not record.id else record.id

        # Ensure UUID object for asyncpg
        try:
            record_uuid = uuid.UUID(record.id)
        except ValueError:
            raise ValueError(f"HiDB: Invalid UUID format: {record.id}")

        # Postgres
        # Schema: id, embedding, content, confidence, decay_rate, source
        query = """
            INSERT INTO memories (id, embedding, content, confidence, decay_rate, source)
            VALUES ($1, $2, $3, $4, $5, $6)
        """

        await self.pool.execute(
            query,
            record_uuid,
            record.embedding, # pgvector handles list[float] automatically after registration
            record.content,
            record.confidence,
            record.decay_rate,
            record.source
        )

        # Redis Cache
        if self.redis:
            try:
                key = f"memory:{record.id}"
                await self.redis.set(key, json.dumps(record.to_dict()), ex=3600)
            except Exception as e:
                logger.error(f"HiDB: Redis insert failed: {e}")

        return record.id

    async def semantic_search(self, vector: List[float], k: int = 5) -> List[MemoryRecord]:
        """
        Search for memories semantically similar to the query vector.

        Args:
            vector: Query embedding vector
            k: Number of results to return

        Returns:
            List of MemoryRecord objects
        """
        if not self.pool:
            await self.connect()
            if not self.pool:
                raise RuntimeError("HiDB: Not connected to database")

        # pgvector syntax for cosine distance is <=>
        query = """
            SELECT id, embedding, content, confidence, decay_rate, source, created_at, updated_at
            FROM memories
            ORDER BY embedding <=> $1
            LIMIT $2
        """

        rows = await self.pool.fetch(query, vector, k)

        results = []
        for r in rows:
            # Parse embedding if returned as string, though asyncpg + pgvector usually returns list/array
            emb = r['embedding']
            if isinstance(emb, str):
                 emb = json.loads(emb) # Fallback

            results.append(
                MemoryRecord(
                    id=str(r['id']),
                    embedding=emb,
                    content=r['content'],
                    confidence=r['confidence'],
                    decay_rate=r['decay_rate'],
                    source=r['source'],
                    created_at=r['created_at'],
                    updated_at=r['updated_at']
                )
            )

        return results
