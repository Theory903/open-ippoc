from sqlalchemy import Column, String, Float, DateTime, ForeignKey
from sqlalchemy.orm import declarative_base, relationship
from sqlalchemy.dialects.postgresql import UUID
from pgvector.sqlalchemy import Vector
from datetime import datetime
import uuid

Base = declarative_base()

class Memory(Base):
    """
    Represents a stored memory with vector embedding.
    Corresponds to 'memories' table in 001_init.sql.
    """
    __tablename__ = "memories"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    embedding = Column(Vector(768))  # Dimension as per schema
    content = Column(String, nullable=False)
    confidence = Column(Float, default=1.0)
    decay_rate = Column(Float, default=0.1)
    source = Column(String, nullable=False)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    # Relationships
    outgoing_links = relationship("CausalLink", foreign_keys="CausalLink.from_memory_id", back_populates="source_memory", cascade="all, delete-orphan")
    incoming_links = relationship("CausalLink", foreign_keys="CausalLink.to_memory_id", back_populates="target_memory", cascade="all, delete-orphan")

class CausalLink(Base):
    """
    Represents a causal link between two memories.
    Corresponds to 'causal_links' table in 001_init.sql.
    """
    __tablename__ = "causal_links"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    from_memory_id = Column(UUID(as_uuid=True), ForeignKey("memories.id", ondelete="CASCADE"))
    to_memory_id = Column(UUID(as_uuid=True), ForeignKey("memories.id", ondelete="CASCADE"))
    strength = Column(Float, default=1.0)
    created_at = Column(DateTime, default=datetime.utcnow)

    # Relationships
    source_memory = relationship("Memory", foreign_keys=[from_memory_id], back_populates="outgoing_links")
    target_memory = relationship("Memory", foreign_keys=[to_memory_id], back_populates="incoming_links")
