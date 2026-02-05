import os
import uuid
import logging
from datetime import datetime
from typing import List, Dict, Any, Optional

from sqlalchemy import Column, String, Float, DateTime, select, text
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession
from sqlalchemy.orm import sessionmaker, declarative_base
from pgvector.sqlalchemy import Vector
import redis.asyncio as redis

logger = logging.getLogger(__name__)
Base = declarative_base()

class Memory(Base):
    __tablename__ = "memories"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    embedding = Column(Vector(768))
    content = Column(String, nullable=False)
    confidence = Column(Float, default=1.0)
    decay_rate = Column(Float, default=0.1)
    source = Column(String, nullable=False)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

class HiDB:
    """
    The Cognitive Substrate (Vector Database).
    Abstracts PostgreSQL/pgvector and Redis into a single Memory interface.
    """
    def __init__(self, db_url: str = None, redis_url: str = None, echo: bool = False):
        self.db_url = db_url or os.getenv("DATABASE_URL", "postgresql+asyncpg://user:pass@localhost:5432/ippoc_hidb")
        self.redis_url = redis_url or os.getenv("REDIS_URL", "redis://localhost:6379")
        self.echo = echo

        self._engine = None
        self._async_session = None
        self._redis = None

    @property
    def engine(self):
        if self._engine is None:
            self._engine = create_async_engine(self.db_url, echo=self.echo)
        return self._engine

    @property
    def async_session(self):
        if self._async_session is None:
            self._async_session = sessionmaker(
                self.engine, class_=AsyncSession, expire_on_commit=False
            )
        return self._async_session

    @property
    def redis(self):
        if self._redis is None:
            self._redis = redis.from_url(self.redis_url, decode_responses=True)
        return self._redis

    async def init_db(self):
        """Initialize the database schema."""
        async with self.engine.begin() as conn:
            # Create extension if not exists (requires superuser, might fail if not)
            try:
                await conn.execute(text("CREATE EXTENSION IF NOT EXISTS vector"))
                await conn.execute(text('CREATE EXTENSION IF NOT EXISTS "uuid-ossp"'))
            except Exception as e:
                logger.warning(f"Could not create extensions: {e}")

            await conn.run_sync(Base.metadata.create_all)

    async def insert_memory(self, content: str, embedding: List[float], source: str = "system",
                          metadata: Dict = None, confidence: float = 1.0) -> str:
        """
        Insert a new memory record.

        Args:
            content: Text content of the memory
            embedding: Vector embedding
            source: Source of the memory
            metadata: Additional metadata (currently not in schema but can be extended)
            confidence: Confidence score

        Returns:
            Memory ID (UUID string)
        """
        try:
            async with self.async_session() as session:
                memory = Memory(
                    content=content,
                    embedding=embedding,
                    source=source,
                    confidence=confidence,
                    # metadata is not in schema, ignoring for now or could add to content/log
                )
                session.add(memory)
                await session.commit()
                return str(memory.id)
        except Exception as e:
            logger.error(f"Failed to insert memory: {e}")
            raise

    async def semantic_search(self, vector: List[float], k: int = 5) -> List[Dict[str, Any]]:
        """
        Search for memories semantically similar to the vector.

        Args:
            vector: Query vector
            k: Number of results to return

        Returns:
            List of memory records
        """
        try:
            async with self.async_session() as session:
                # Using cosine distance for similarity search
                # Order by cosine distance ascending (closest first)
                stmt = select(Memory).order_by(Memory.embedding.cosine_distance(vector)).limit(k)

                result = await session.execute(stmt)
                memories = result.scalars().all()

                results = []
                for m in memories:
                    results.append({
                        "id": str(m.id),
                        "content": m.content,
                        "source": m.source,
                        "confidence": m.confidence,
                        "created_at": m.created_at.isoformat() if m.created_at else None,
                    })

                return results
        except Exception as e:
            logger.error(f"Semantic search failed: {e}")
            raise

    async def close(self):
        """Close connections."""
        if self._engine:
            await self._engine.dispose()
        if self._redis:
            await self._redis.close()
