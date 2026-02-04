from datetime import datetime
from typing import List, Dict, Any, Optional
from sqlalchemy import Column, Integer, String, JSON, DateTime, select, text
from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession
from sqlalchemy.orm import sessionmaker, declarative_base
import os

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
    def __init__(self, db_url: str = None):
        self.db_url = db_url or os.getenv("DATABASE_URL", "postgresql+asyncpg://user:pass@localhost:5432/ippoc")
        self.engine = create_async_engine(self.db_url, echo=False)
        self.async_session = sessionmaker(
            self.engine, class_=AsyncSession, expire_on_commit=False
        )

    async def init_db(self):
        async with self.engine.begin() as conn:
            await conn.run_sync(Base.metadata.create_all)

    async def write(self, content: str, source: str = "openclaw", modality: str = "text", metadata: Dict = None):
        async with self.async_session() as session:
            event = EpisodicEvent(
                content=content,
                source=source,
                modality=modality,
                metadata_=metadata or {}
            )
            session.add(event)
            await session.commit()
            return event.id

    async def search(self, query: str = None, limit: int = 10) -> List[Dict[str, Any]]:
        """
        Simple keyword search or recent retrieval from episodic log
        """
        async with self.async_session() as session:
            stmt = select(EpisodicEvent).order_by(EpisodicEvent.timestamp.desc()).limit(limit)
            
            if query:
                # Basic wildcard match for now (Full Text Search would be better later)
                stmt = stmt.where(EpisodicEvent.content.ilike(f"%{query}%"))
            
            result = await session.execute(stmt)
            events = result.scalars().all()
            
            return [{
                "content": e.content,
                "score": 1.0, # Recency bias implicitly high
                "metadata": {
                    "timestamp": e.timestamp.isoformat(),
                    "source": e.source,
                    "id": e.id
                },
                "type": "episodic"
            } for e in events]
