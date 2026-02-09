from datetime import datetime
from typing import List, Dict, Any, Optional
from sqlalchemy import Column, Integer, String, JSON, DateTime, select, text
from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession
from sqlalchemy.orm import sessionmaker, declarative_base
import os
import logging

logger = logging.getLogger(__name__)
Base = declarative_base()

class EpisodicEvent(Base):
    """Raw Log of Events (The Application Journal)"""
    __tablename__ = "episodic_log"

    id = Column(Integer, primary_key=True, index=True)
    timestamp = Column(DateTime, default=datetime.utcnow, index=True)
    source = Column(String, index=True)  # e.g., "openclaw", "shell"
    modality = Column(String)            # "text", "code", "cmd"
    content = Column(String)             # The actual text
    metadata_ = Column("metadata", JSON) # Extra context

class EpisodicManager:
    def __init__(self, db_url: str = None, echo: bool = False):
        self.db_url = db_url or os.getenv("DATABASE_URL", "postgresql+asyncpg://user:pass@localhost:5432/ippoc")
        self.echo = echo
        self._engine = None
        self._async_session = None
        
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

    async def init_db(self):
        async with self.engine.begin() as conn:
            await conn.run_sync(Base.metadata.create_all)

    async def write(self, content: str, source: str = "openclaw", modality: str = "text", metadata: Dict = None) -> int:
        """
        Store an episodic event.
        
        Args:
            content: Event content
            source: Event source
            modality: Content type
            metadata: Additional metadata
            
        Returns:
            Event ID
        
        Raises:
            Exception: If database operation fails
        """
        try:
            async with self.async_session() as session:
                event = EpisodicEvent(
                    content=content,
                    source=source,
                    modality=modality,
                    metadata_=metadata or {}
                )
                session.add(event)
                await session.commit()
                logger.debug(f"Stored episodic event ID: {event.id}")
                return event.id
        except Exception as e:
            logger.error(f"Failed to store episodic event: {e}")
            raise

    async def search(self, query: str = None, limit: int = 10, source: str = None) -> List[Dict[str, Any]]:
        """
        Search episodic memory with filters.
        
        Args:
            query: Text to search for
            limit: Maximum results
            source: Filter by source
            
        Returns:
            List of matching events with relevance scores
        """
        try:
            async with self.async_session() as session:
                stmt = select(EpisodicEvent).order_by(EpisodicEvent.timestamp.desc()).limit(limit)
                
                # Apply filters
                if query:
                    stmt = stmt.where(EpisodicEvent.content.ilike(f"%{query}%"))
                
                if source:
                    stmt = stmt.where(EpisodicEvent.source == source)
                
                result = await session.execute(stmt)
                events = result.scalars().all()
                
                results = []
                for e in events:
                    # Calculate relevance score
                    base_score = 1.0
                    if query:
                        # Boost score based on query match quality
                        content_lower = e.content.lower()
                        query_lower = query.lower()
                        if query_lower in content_lower:
                            # Exact match bonus
                            base_score += 0.5
                        elif any(word in content_lower for word in query_lower.split()):
                            # Partial match bonus
                            base_score += 0.2
                    
                    results.append({
                        "content": e.content,
                        "score": base_score,
                        "metadata": {
                            "timestamp": e.timestamp.isoformat(),
                            "source": e.source,
                            "modality": e.modality,
                            "id": e.id
                        },
                        "type": "episodic"
                    })
                
                logger.debug(f"Found {len(results)} episodic events for query: {query}")
                return results
                
        except Exception as e:
            logger.error(f"Episodic search failed: {e}")
            return []
    
    async def get_recent(self, limit: int = 10, hours: int = None) -> List[Dict[str, Any]]:
        """
        Get recent events, optionally filtered by time.
        
        Args:
            limit: Maximum events to return
            hours: Hours back to look (None for all)
            
        Returns:
            Recent events ordered by timestamp
        """
        try:
            async with self.async_session() as session:
                stmt = select(EpisodicEvent).order_by(EpisodicEvent.timestamp.desc()).limit(limit)
                
                if hours:
                    from datetime import timedelta
                    cutoff = datetime.utcnow() - timedelta(hours=hours)
                    stmt = stmt.where(EpisodicEvent.timestamp >= cutoff)
                
                result = await session.execute(stmt)
                events = result.scalars().all()
                
                return [{
                    "content": e.content,
                    "metadata": {
                        "timestamp": e.timestamp.isoformat(),
                        "source": e.source,
                        "modality": e.modality,
                        "id": e.id
                    }
                } for e in events]
                
        except Exception as e:
            logger.error(f"Failed to get recent events: {e}")
            return []
    
    async def stats(self) -> Dict[str, Any]:
        """Get episodic memory statistics"""
        try:
            async with self.async_session() as session:
                # Total events
                total_stmt = select(EpisodicEvent)
                total_result = await session.execute(total_stmt)
                total_count = len(total_result.scalars().all())
                
                # Events by source
                from sqlalchemy import func
                source_stmt = select(EpisodicEvent.source, func.count(EpisodicEvent.id)).group_by(EpisodicEvent.source)
                source_result = await session.execute(source_stmt)
                sources = dict(source_result.fetchall())
                
                return {
                    "total_events": total_count,
                    "events_by_source": sources,
                    "timestamp": datetime.now().isoformat()
                }
        except Exception as e:
            logger.error(f"Failed to get episodic stats: {e}")
            return {"error": str(e)}
