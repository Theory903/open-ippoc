"""
Core Memory System - Unified Interface for All Memory Operations

This module provides a single entrypoint for accessing all memory subsystems:
- Episodic Memory (events, experiences)
- Semantic Memory (facts, concepts)  
- Procedural Memory (skills, procedures)
- Graph Memory (relationships, causality)

Usage:
    from mnemosyne import memory
    
    # Store an experience
    await memory.store_episodic("User asked about Python", source="chat")
    
    # Recall relevant information
    results = await memory.recall("Python programming")
    
    # Search for skills
    skills = await memory.find_skill("data analysis")
"""

import asyncio
from typing import List, Dict, Any, Optional, Union
from collections import defaultdict
from dataclasses import dataclass
from datetime import datetime

# Import all memory managers
from .episodic.manager import EpisodicManager
from .semantic.rag import SemanticManager
from .procedural.manager import ProceduralManager
from .graph.manager import GraphManager

@dataclass
class MemoryFragment:
    """Unified representation of a memory unit"""
    type: str  # "episodic", "semantic", "procedural", "graph"
    content: str
    metadata: Dict[str, Any]
    score: float = 1.0
    timestamp: Optional[datetime] = None
    id: Optional[str] = None

class MemorySystem:
    """
    Unified Memory Interface for the IPPOC organism.
    
    Coordinates all memory subsystems and provides:
    - Single-point access for storage and retrieval
    - Cross-memory search capabilities
    - Memory consolidation and pruning
    - Context-aware recall
    """
    
    def __init__(self, db_url: str = None, vector_store=None, embeddings=None):
        """
        Initialize the complete memory system.
        
        Args:
            db_url: Database connection string for SQL-based stores
            vector_store: Vector store instance for semantic memory
            embeddings: Embedding model for vector operations
        """
        # Initialize individual managers
        self.episodic = EpisodicManager(db_url)
        self.graph = GraphManager(db_url)
        
        # Semantic and procedural depend on vector store
        if vector_store and embeddings:
            self.semantic = SemanticManager(vector_store, embeddings)
            self.procedural = ProceduralManager(self.semantic)
        else:
            self.semantic = None
            self.procedural = None
            
        self._initialized = False
    
    async def initialize(self):
        """Initialize all memory subsystems"""
        if self._initialized:
            return
            
        # Initialize SQL-based stores
        await self.episodic.init_db()
        await self.graph.init_db()
        
        self._initialized = True
    
    async def store_episodic(self, content: str, source: str = "system", 
                           modality: str = "text", metadata: Dict = None) -> str:
        """
        Store an episodic memory (experience/event).
        
        Args:
            content: The memory content
            source: Origin of the memory (e.g., "user", "tool", "system")
            modality: Type of content ("text", "code", "image", etc.)
            metadata: Additional context
            
        Returns:
            Memory ID
        """
        await self.initialize()
        event_id = await self.episodic.write(content, source, modality, metadata)
        return f"episodic:{event_id}"
    
    async def store_semantic(self, content: str, metadata: Dict = None) -> List[str]:
        """
        Store semantic knowledge (facts, concepts).
        
        Args:
            content: The factual content
            metadata: Additional metadata
            
        Returns:
            List of stored document IDs
        """
        if not self.semantic:
            raise RuntimeError("Semantic memory not configured - missing vector store/embeddings")
            
        await self.initialize()
        return await self.semantic.add_memory(content, metadata or {})
    
    async def register_skill(self, name: str, code: str, description: str, 
                           language: str = "python") -> str:
        """
        Register a procedural skill.
        
        Args:
            name: Skill identifier
            code: Implementation code
            description: Natural language description
            language: Programming language
            
        Returns:
            Confirmation message
        """
        if not self.procedural:
            raise RuntimeError("Procedural memory not configured")
            
        await self.initialize()
        return await self.procedural.register_skill(name, code, description, language)
    
    async def add_relation(self, source: str, relation: str, target: str,
                          source_type: str = "Concept", target_type: str = "Concept") -> str:
        """
        Add a relationship to the knowledge graph.
        
        Args:
            source: Source entity
            relation: Relationship type
            target: Target entity
            source_type: Type of source entity
            target_type: Type of target entity
            
        Returns:
            Status message
        """
        await self.initialize()
        return await self.graph.add_triple(source, relation, target, source_type, target_type)
    
    async def recall(self, query: str, limit: int = 10, include_types: List[str] = None) -> List[MemoryFragment]:
        """
        Comprehensive memory recall across all subsystems.
        
        Args:
            query: Search query
            limit: Maximum results to return
            include_types: Memory types to include ["episodic", "semantic", "procedural", "graph"]
            
        Returns:
            List of relevant memory fragments
        """
        await self.initialize()
        
        if include_types is None:
            include_types = ["episodic", "semantic", "procedural", "graph"]
            
        tasks = []
        
        # Search episodic memory
        if "episodic" in include_types:
            tasks.append(self._search_episodic(query, limit // 2))
            
        # Search semantic memory
        if "semantic" in include_types and self.semantic:
            tasks.append(self._search_semantic(query, limit // 2))
            
        # Search procedural memory
        if "procedural" in include_types and self.procedural:
            tasks.append(self._search_procedural(query, limit // 3))
            
        # Search graph memory
        if "graph" in include_types:
            tasks.append(self._search_graph(query, limit // 3))
        
        # Execute all searches concurrently
        results = await asyncio.gather(*tasks, return_exceptions=True)
        
        # Combine and rank results
        fragments = []
        for result in results:
            if isinstance(result, Exception):
                continue
            if result:
                fragments.extend(result)
        
        # Sort by relevance score and limit
        fragments.sort(key=lambda x: x.score, reverse=True)
        return fragments[:limit]
    
    async def _search_episodic(self, query: str, limit: int) -> List[MemoryFragment]:
        """Search episodic memory"""
        events = await self.episodic.search(query, limit)
        return [
            MemoryFragment(
                type="episodic",
                content=event["content"],
                metadata=event["metadata"],
                score=event["score"],
                timestamp=datetime.fromisoformat(event["metadata"]["timestamp"]),
                id=f"episodic:{event['metadata']['id']}"
            ) for event in events
        ]
    
    async def _search_semantic(self, query: str, limit: int) -> List[MemoryFragment]:
        """Search semantic memory"""
        documents = await self.semantic.retrieve_relevant(query, limit)
        return [
            MemoryFragment(
                type="semantic",
                content=doc.page_content,
                metadata=doc.metadata,
                score=doc.metadata.get("retrieval_score", 1.0),
                id=doc.metadata.get("id", f"semantic:{i}")
            ) for i, doc in enumerate(documents)
        ]
    
    async def _search_procedural(self, query: str, limit: int) -> List[MemoryFragment]:
        """Search procedural memory"""
        skills = await self.procedural.find_skill(query)
        return [
            MemoryFragment(
                type="procedural",
                content=skill.get("content", ""),
                metadata=skill.get("metadata", {}),
                score=skill.get("score", 1.0),
                id=skill.get("id", f"procedural:{i}")
            ) for i, skill in enumerate(skills)
        ]
    
    async def _search_graph(self, query: str, limit: int) -> List[MemoryFragment]:
        """Search graph memory"""
        relations = await self.graph.get_neighbors(query)
        return [
            MemoryFragment(
                type="graph",
                content=rel,
                metadata={"entity": query},
                score=0.8,  # Graph relations have medium confidence
                id=f"graph:{i}"
            ) for i, rel in enumerate(relations[:limit])
        ]
    
    async def get_context(self, entity: str, depth: int = 1) -> Dict[str, Any]:
        """
        Get contextual information about an entity from the knowledge graph.
        
        Args:
            entity: Entity to query
            depth: Depth of relationship traversal
            
        Returns:
            Context information including neighbors and properties
        """
        await self.initialize()
        neighbors = await self.graph.get_neighbors(entity)
        
        return {
            "entity": entity,
            "relations": neighbors,
            "type": "concept",  # Could be enhanced with entity typing
            "timestamp": datetime.now().isoformat()
        }
    
    async def forget(self, criteria: Dict[str, Any]) -> int:
        """
        Remove memories matching criteria.
        
        Args:
            criteria: Deletion criteria. Supported keys:
                - id: Specific memory ID (e.g., "episodic:123")
                - ids: List of IDs
                - type: Subsystem type ("episodic", "semantic", "procedural", "graph")

                For type="episodic":
                    - time_range: (start, end)
                    - source: string

                For type="semantic":
                    - ids: List of document IDs (if not passed globally)

                For type="procedural":
                    - name: Skill name

                For type="graph":
                    - entity: Entity name
            
        Returns:
            Number of memories removed
        """
        count = 0
        await self.initialize()

        # Helper to extract IDs
        target_ids = []
        if "id" in criteria:
            target_ids.append(criteria["id"])
        if "ids" in criteria:
            target_ids.extend(criteria["ids"])

        ids_by_type = defaultdict(list)

        # 1. Parse IDs with prefixes
        unprefixed_ids = []
        for mid in target_ids:
            if isinstance(mid, str) and ":" in mid:
                prefix, real_id = mid.split(":", 1)
                ids_by_type[prefix].append(real_id)
            else:
                unprefixed_ids.append(mid)

        # 2. If type is specified, assign unprefixed IDs to that type
        if "type" in criteria:
            m_type = criteria["type"]
            if unprefixed_ids:
                ids_by_type[m_type].extend(unprefixed_ids)

        # 3. Execute Deletions based on ids_by_type
        if ids_by_type["episodic"]:
            e_ids = []
            for i in ids_by_type["episodic"]:
                if str(i).isdigit():
                    e_ids.append(int(i))
            if e_ids:
                count += await self.episodic.delete(ids=e_ids)

        if ids_by_type["semantic"] and self.semantic:
            success = await self.semantic.delete_memories(ids_by_type["semantic"])
            if success:
                count += len(ids_by_type["semantic"])

        # 4. Handle other criteria based on type
        if "type" in criteria:
            m_type = criteria["type"]

            if m_type == "episodic":
                # Handle time_range, source
                # Avoid passing 'ids' again if we already handled them via ids_by_type
                delete_kwargs = {k: v for k, v in criteria.items() if k not in ["type", "id", "ids"]}
                if delete_kwargs:
                    count += await self.episodic.delete(**delete_kwargs)

            elif m_type == "procedural" and self.procedural:
                if "name" in criteria:
                    success = await self.procedural.unregister_skill(criteria["name"])
                    if success:
                        count += 1

            elif m_type == "graph":
                if "entity" in criteria:
                    success = await self.graph.delete_entity(criteria["entity"])
                    if success:
                        count += 1

        return count
    
    def health_check(self) -> Dict[str, Any]:
        """Check memory system health"""
        return {
            "initialized": self._initialized,
            "episodic_enabled": True,
            "semantic_enabled": self.semantic is not None,
            "procedural_enabled": self.procedural is not None,
            "graph_enabled": True,
            "timestamp": datetime.now().isoformat()
        }

# Global singleton instance
_memory_system: Optional[MemorySystem] = None

def get_memory_system(**kwargs) -> MemorySystem:
    """Get or create the global memory system instance"""
    global _memory_system
    if _memory_system is None:
        _memory_system = MemorySystem(**kwargs)
    return _memory_system