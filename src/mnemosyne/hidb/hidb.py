import logging
import os
from typing import List, Dict, Optional, Any
from uuid import UUID

from sqlalchemy import select, delete
from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession, AsyncEngine
from sqlalchemy.orm import sessionmaker, selectinload
from sqlalchemy.exc import SQLAlchemyError

from .models import Base, Memory, CausalLink

logger = logging.getLogger(__name__)

class HiDB:
    """
    The "Past" of the organism.
    Interface to the Hierarchical Database (Postgres + pgvector).
    """
    def __init__(self, db_url: str = None, echo: bool = False):
        self.db_url = db_url or os.getenv("DATABASE_URL", "postgresql+asyncpg://user:pass@localhost:5432/ippoc_hidb")
        self.echo = echo
        self._engine: Optional[AsyncEngine] = None
        self._async_session: Optional[sessionmaker] = None

    @property
    def engine(self) -> AsyncEngine:
        if self._engine is None:
            self._engine = create_async_engine(self.db_url, echo=self.echo)
        return self._engine

    @property
    def async_session(self) -> sessionmaker:
        if self._async_session is None:
            self._async_session = sessionmaker(
                self.engine, class_=AsyncSession, expire_on_commit=False
            )
        return self._async_session

    async def init_db(self):
        """Initialize database tables"""
        async with self.engine.begin() as conn:
            # We don't drop tables, just create if not exists
            # Note: This requires pgvector extension to be installed in the DB
            await conn.run_sync(Base.metadata.create_all)
            logger.info("HiDB tables initialized")

    async def store_memory(
        self,
        content: str,
        embedding: List[float],
        source: str,
        confidence: float = 1.0,
        decay_rate: float = 0.1
    ) -> UUID:
        """
        Store a new memory with vector embedding.
        """
        try:
            async with self.async_session() as session:
                memory = Memory(
                    content=content,
                    embedding=embedding,
                    source=source,
                    confidence=confidence,
                    decay_rate=decay_rate
                )
                session.add(memory)
                await session.commit()
                await session.refresh(memory)
                logger.debug(f"Stored memory {memory.id}")
                return memory.id
        except SQLAlchemyError as e:
            logger.error(f"Failed to store memory: {e}")
            raise

    async def search_memories(
        self,
        query_embedding: List[float],
        limit: int = 10,
        min_confidence: float = 0.0
    ) -> List[Memory]:
        """
        Search for memories similar to the query embedding.
        """
        try:
            async with self.async_session() as session:
                stmt = select(Memory).where(Memory.confidence >= min_confidence)

                # Order by cosine distance (using <=> operator via pgvector)
                stmt = stmt.order_by(Memory.embedding.cosine_distance(query_embedding)).limit(limit)

                result = await session.execute(stmt)
                return result.scalars().all()
        except SQLAlchemyError as e:
            logger.error(f"Failed to search memories: {e}")
            raise

    async def link_memories(self, source_id: UUID, target_id: UUID, strength: float = 1.0) -> UUID:
        """
        Create a causal link between two memories.
        """
        try:
            async with self.async_session() as session:
                link = CausalLink(
                    from_memory_id=source_id,
                    to_memory_id=target_id,
                    strength=strength
                )
                session.add(link)
                await session.commit()
                await session.refresh(link)
                logger.debug(f"Linked memory {source_id} -> {target_id}")
                return link.id
        except SQLAlchemyError as e:
            logger.error(f"Failed to link memories: {e}")
            raise

    async def get_memory(self, memory_id: UUID) -> Optional[Memory]:
        """Get a specific memory by ID"""
        try:
            async with self.async_session() as session:
                result = await session.execute(select(Memory).where(Memory.id == memory_id))
                return result.scalar_one_or_none()
        except SQLAlchemyError as e:
            logger.error(f"Failed to get memory: {e}")
            raise

    async def get_context(self, memory_id: UUID, direction: str = "both") -> Dict[str, List[CausalLink]]:
        """
        Get connected memories (context).
        direction: 'outgoing', 'incoming', or 'both'
        """
        try:
            async with self.async_session() as session:
                context = {"outgoing": [], "incoming": []}

                if direction in ["outgoing", "both"]:
                    stmt = select(CausalLink).where(CausalLink.from_memory_id == memory_id)
                    # We should probably eagerly load the target_memory
                    stmt = stmt.options(selectinload(CausalLink.target_memory))
                    result = await session.execute(stmt)
                    context["outgoing"] = result.scalars().all()

                if direction in ["incoming", "both"]:
                    stmt = select(CausalLink).where(CausalLink.to_memory_id == memory_id)
                    stmt = stmt.options(selectinload(CausalLink.source_memory))
                    result = await session.execute(stmt)
                    context["incoming"] = result.scalars().all()

                return context
        except SQLAlchemyError as e:
            logger.error(f"Failed to get context: {e}")
            raise

    async def delete_memory(self, memory_id: UUID) -> bool:
        """Delete a memory and its links"""
        try:
            async with self.async_session() as session:
                # Due to cascade, links should be deleted automatically
                await session.execute(delete(Memory).where(Memory.id == memory_id))
                await session.commit()
                return True
        except SQLAlchemyError as e:
            logger.error(f"Failed to delete memory: {e}")
            raise
