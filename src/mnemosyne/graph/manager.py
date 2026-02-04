from typing import List, Dict, Any, Tuple, Optional
from sqlalchemy import Column, Integer, String, Float, ForeignKey, text, DateTime
from sqlalchemy.orm import relationship
from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession
from sqlalchemy.orm import sessionmaker, declarative_base
import os
import logging
from datetime import datetime

logger = logging.getLogger(__name__)
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
        self._initialized = False

    async def init_db(self):
        if self._initialized:
            return
        async with self.engine.begin() as conn:
            await conn.run_sync(Base.metadata.create_all)
        self._initialized = True

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
        await self.init_db()
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
    
    async def find_relationship_path(self, source_entity: str, target_entity: str, max_depth: int = 3) -> List[Dict[str, Any]]:
        """
        Find paths between two entities in the knowledge graph.
        
        Args:
            source_entity: Starting entity name
            target_entity: Target entity name
            max_depth: Maximum path depth to search
            
        Returns:
            List of relationship paths with metadata
        """
        await self.init_db()
        paths = []
        
        try:
            async with self.Session() as session:
                # Get entity IDs
                source_res = await session.execute(
                    text("SELECT id FROM kg_entities WHERE name = :name"), 
                    {"name": source_entity}
                )
                source_row = source_res.fetchone()
                if not source_row:
                    return []
                source_id = source_row[0]
                
                target_res = await session.execute(
                    text("SELECT id FROM kg_entities WHERE name = :name"), 
                    {"name": target_entity}
                )
                target_row = target_res.fetchone()
                if not target_row:
                    return []
                target_id = target_row[0]
                
                # BFS to find paths
                paths = await self._bfs_find_paths(session, source_id, target_id, max_depth)
                
            return paths
            
        except Exception as e:
            logger.error(f"Path finding failed: {e}")
            return []
    
    async def _bfs_find_paths(self, session: AsyncSession, source_id: int, target_id: int, max_depth: int) -> List[Dict[str, Any]]:
        """BFS algorithm to find paths between entities"""
        from collections import deque
        
        paths = []
        queue = deque([(source_id, [], 0)])  # (current_id, path_edges, depth)
        visited = {source_id}
        
        while queue and len(paths) < 10:  # Limit to 10 paths
            current_id, path_edges, depth = queue.popleft()
            
            if depth >= max_depth:
                continue
            
            # Get outgoing relations
            stmt = text("""
                SELECT r.target_id, r.relation, e.name
                FROM kg_relations r
                JOIN kg_entities e ON r.target_id = e.id
                WHERE r.source_id = :source_id
            """)
            result = await session.execute(stmt, {"source_id": current_id})
            
            for target_id_result, relation, target_name in result.fetchall():
                new_edge = {
                    "from": current_id,
                    "to": target_id_result,
                    "relation": relation,
                    "target_name": target_name
                }
                new_path = path_edges + [new_edge]
                
                if target_id_result == target_id:
                    # Found target - reconstruct full path
                    full_path = await self._reconstruct_path(session, new_path)
                    paths.append(full_path)
                elif target_id_result not in visited:
                    visited.add(target_id_result)
                    queue.append((target_id_result, new_path, depth + 1))
        
        return paths
    
    async def _reconstruct_path(self, session: AsyncSession, path_edges: List[Dict]) -> Dict[str, Any]:
        """Reconstruct full path with entity names"""
        nodes = []
        relations = []
        
        if path_edges:
            # Get source entity name
            first_edge = path_edges[0]
            source_stmt = text("SELECT name FROM kg_entities WHERE id = :id")
            source_res = await session.execute(source_stmt, {"id": first_edge["from"]})
            source_row = source_res.fetchone()
            if source_row:
                nodes.append(source_row[0])
            
            # Add intermediate nodes and relations
            for edge in path_edges:
                relations.append(edge["relation"])
                nodes.append(edge["target_name"])
        
        return {
            "nodes": nodes,
            "relations": relations,
            "length": len(relations),
            "confidence": 1.0 - (len(relations) * 0.1)  # Decrease confidence with path length
        }
    
    async def get_entity_context(self, entity_name: str, context_types: List[str] = None) -> Dict[str, Any]:
        """
        Get comprehensive context for an entity including relationships and metadata.
        
        Args:
            entity_name: Entity to get context for
            context_types: Types of context to include ['relationships', 'attributes', 'history']
            
        Returns:
            Dictionary with entity context information
        """
        if context_types is None:
            context_types = ['relationships', 'attributes']
            
        await self.init_db()
        context = {"entity": entity_name}
        
        try:
            async with self.Session() as session:
                # Get entity details
                entity_stmt = text("""
                    SELECT id, type, metadata_
                    FROM kg_entities
                    WHERE name = :name
                """)
                entity_res = await session.execute(entity_stmt, {"name": entity_name})
                entity_row = entity_res.fetchone()
                
                if not entity_row:
                    return {"error": f"Entity '{entity_name}' not found"}
                
                entity_id, entity_type, metadata_str = entity_row
                context["type"] = entity_type
                
                # Parse metadata
                try:
                    context["metadata"] = json.loads(metadata_str) if metadata_str else {}
                except:
                    context["metadata"] = {}
                
                # Get relationships if requested
                if 'relationships' in context_types:
                    # Incoming relationships
                    incoming_stmt = text("""
                        SELECT e.name, r.relation
                        FROM kg_relations r
                        JOIN kg_entities e ON r.source_id = e.id
                        WHERE r.target_id = :entity_id
                    """)
                    incoming_res = await session.execute(incoming_stmt, {"entity_id": entity_id})
                    context["incoming_relations"] = [
                        {"from": row[0], "relation": row[1]} 
                        for row in incoming_res.fetchall()
                    ]
                    
                    # Outgoing relationships
                    outgoing_stmt = text("""
                        SELECT e.name, r.relation
                        FROM kg_relations r
                        JOIN kg_entities e ON r.target_id = e.id
                        WHERE r.source_id = :entity_id
                    """)
                    outgoing_res = await session.execute(outgoing_stmt, {"entity_id": entity_id})
                    context["outgoing_relations"] = [
                        {"to": row[0], "relation": row[1]} 
                        for row in outgoing_res.fetchall()
                    ]
                
                # Get attributes if requested
                if 'attributes' in context_types:
                    # This would query attribute nodes connected to the entity
                    attr_stmt = text("""
                        SELECT e.name, r.relation
                        FROM kg_relations r
                        JOIN kg_entities e ON e.id = r.target_id
                        WHERE r.source_id = :entity_id
                        AND r.relation IN ('has_attribute', 'described_as', 'characterized_by')
                    """)
                    attr_res = await session.execute(attr_stmt, {"entity_id": entity_id})
                    context["attributes"] = [
                        {"attribute": row[0], "type": row[1]}
                        for row in attr_res.fetchall()
                    ]
                
                context["timestamp"] = datetime.now().isoformat()
                
            return context
            
        except Exception as e:
            logger.error(f"Entity context retrieval failed: {e}")
            return {"error": str(e)}
    
    async def find_similar_entities(self, entity_name: str, similarity_threshold: float = 0.7) -> List[Dict[str, Any]]:
        """
        Find entities similar to the given entity based on shared relationships.
        
        Args:
            entity_name: Reference entity
            similarity_threshold: Minimum similarity score (0.0 to 1.0)
            
        Returns:
            List of similar entities with similarity scores
        """
        await self.init_db()
        similar_entities = []
        
        try:
            async with self.Session() as session:
                # Get reference entity relationships
                ref_stmt = text("""
                    SELECT e.name, r.relation
                    FROM kg_relations r
                    JOIN kg_entities e ON e.id = r.target_id
                    WHERE r.source_id = (SELECT id FROM kg_entities WHERE name = :name)
                """)
                ref_res = await session.execute(ref_stmt, {"name": entity_name})
                ref_relations = set(f"{row[0]}:{row[1]}" for row in ref_res.fetchall())
                
                if not ref_relations:
                    return []
                
                # Compare with all other entities
                all_entities_stmt = text("SELECT id, name FROM kg_entities WHERE name != :name")
                all_entities_res = await session.execute(all_entities_stmt, {"name": entity_name})
                
                for entity_id, entity_name_cmp in all_entities_res.fetchall():
                    # Get this entity's relationships
                    cmp_stmt = text("""
                        SELECT e.name, r.relation
                        FROM kg_relations r
                        JOIN kg_entities e ON e.id = r.target_id
                        WHERE r.source_id = :entity_id
                    """)
                    cmp_res = await session.execute(cmp_stmt, {"entity_id": entity_id})
                    cmp_relations = set(f"{row[0]}:{row[1]}" for row in cmp_res.fetchall())
                    
                    # Calculate Jaccard similarity
                    intersection = len(ref_relations & cmp_relations)
                    union = len(ref_relations | cmp_relations)
                    similarity = intersection / union if union > 0 else 0
                    
                    if similarity >= similarity_threshold:
                        similar_entities.append({
                            "entity": entity_name_cmp,
                            "similarity": similarity,
                            "shared_relations": intersection
                        })
                
                # Sort by similarity
                similar_entities.sort(key=lambda x: x["similarity"], reverse=True)
                
            return similar_entities
            
        except Exception as e:
            logger.error(f"Similar entity search failed: {e}")
            return []
