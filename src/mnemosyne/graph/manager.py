from typing import List, Dict, Any, Tuple
from sqlalchemy import Column, Integer, String, Float, ForeignKey, text
from sqlalchemy.orm import relationship
from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession
from sqlalchemy.orm import sessionmaker, declarative_base
import os

Base = declarative_base()

class Entity(Base):
    """A Node in the Knowledge Graph"""
    __tablename__ = "kg_entities"
    id = Column(Integer, primary_key=True)
    name = Column(String, unique=True, index=True)
    type = Column(String) # Person, Location, Concept
    metadata_ = Column("metadata", String) # JSON string

class Relation(Base):
    """An Edge in the Knowledge Graph"""
    __tablename__ = "kg_relations"
    id = Column(Integer, primary_key=True)
    source_id = Column(Integer, ForeignKey("kg_entities.id"))
    target_id = Column(Integer, ForeignKey("kg_entities.id"))
    relation = Column(String) # e.g. "authored", "is_located_in"
    weight = Column(Float, default=1.0)

class GraphManager:
    def __init__(self, db_url: str = None):
        self.db_url = db_url or os.getenv("DATABASE_URL", "postgresql+asyncpg://user:pass@localhost:5432/ippoc")
        self.engine = create_async_engine(self.db_url, echo=False)
        self.Session = sessionmaker(self.engine, class_=AsyncSession, expire_on_commit=False)

    async def init_db(self):
        async with self.engine.begin() as conn:
            await conn.run_sync(Base.metadata.create_all)

    async def add_triple(self, source: str, relation: str, target: str, source_type="Concept", target_type="Concept"):
        """
        Adds (Source) -> [Relation] -> (Target) to the graph.
        Idempotent (get_or_create).
        """
        async with self.Session() as session:
            # Helper to get/create entity
            async def get_or_create(name, type_):
                res = await session.execute(text("SELECT id FROM kg_entities WHERE name = :name"), {"name": name})
                row = res.fetchone()
                if row:
                    return row[0]
                new_ent = Entity(name=name, type=type_)
                session.add(new_ent)
                await session.flush()
                return new_ent.id

            s_id = await get_or_create(source, source_type)
            t_id = await get_or_create(target, target_type)
            
            # Add relation
            # Check if exists
            res = await session.execute(
                text("SELECT id FROM kg_relations WHERE source_id=:s AND target_id=:t AND relation=:r"),
                {"s": s_id, "t": t_id, "r": relation}
            )
            if not res.fetchone():
                rel = Relation(source_id=s_id, target_id=t_id, relation=relation)
                session.add(rel)
                await session.commit()
                return f"Added: ({source}) -[{relation}]-> ({target})"
            return f"Exists: ({source}) -[{relation}]-> ({target})"

    async def get_neighbors(self, entity_name: str) -> List[str]:
        """
        Returns all relations connected to an entity.
        Useful for expanding context (GraphRAG).
        """
        async with self.Session() as session:
            # 1. Find Entity ID
            res = await session.execute(text("SELECT id FROM kg_entities WHERE name = :n"), {"n": entity_name})
            row = res.fetchone()
            if not row:
                return []
            eid = row[0]

            # 2. Find outgoing edges
            stmt = text("""
                SELECT e.name, r.relation 
                FROM kg_relations r 
                JOIN kg_entities e ON r.target_id = e.id 
                WHERE r.source_id = :eid
            """)
            out = await session.execute(stmt, {"eid": eid})
            
            return [f"-[{row[1]}]-> {row[0]}" for row in out.fetchall()]
