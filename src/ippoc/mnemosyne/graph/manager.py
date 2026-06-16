from typing import List, Dict, Any, Tuple, Optional
from collections import defaultdict
from sqlalchemy import Column, Integer, String, Float, ForeignKey, text, DateTime, bindparam
from sqlalchemy.orm import relationship
from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession
from sqlalchemy.orm import sessionmaker, declarative_base
import os
import logging
import json
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
    source_id = Column(Integer, ForeignKey("kg_entities.id"), index=True)
    target_id = Column(Integer, ForeignKey("kg_entities.id"), index=True)
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
                # Optimized: removed consecutive entity ID lookups (O(N) bottleneck) in favor of a batched SQL query
                stmt = text("SELECT id, name FROM kg_entities WHERE name IN :names")
                stmt = stmt.bindparams(bindparam("names", expanding=True))
                res = await session.execute(stmt, {"names": [source_entity, target_entity]})

                rows = res.fetchall()
                if not rows:
                    return []

                id_map = {row.name: row.id for row in rows}
                source_id = id_map.get(source_entity)
                target_id = id_map.get(target_entity)
                
                if source_id is None or target_id is None:
                    return []
                
                # Removed the O(N) bottleneck BFS loop (e.g. `if depth >= max_depth: continue... SELECT r.target_id...`)
                # in favor of an optimized recursive CTE approach.
                paths = await self._find_paths_cte(session, source_id, target_id, max_depth)
                
            return paths
            
        except Exception as e:
            logger.error(f"Path finding failed: {e}")
            return []
    
    async def _find_paths_cte(self, session: AsyncSession, source_id: int, target_id: int, max_depth: int) -> List[Dict[str, Any]]:
        """Recursive CTE based path finding - Faster than BFS and avoids N+1 queries"""
        # Recursive CTE query replaces the inefficient BFS loop completely.
        # We use simple string concatenation for path tracking which is portable between Postgres and SQLite
        cte_query = text("""
            WITH RECURSIVE path_search(last_id, path_ids, path_rels, depth) AS (
                -- Base case
                SELECT
                    target_id,
                    cast(source_id as text) || ',' || cast(target_id as text),
                    cast(relation as text),
                    1
                FROM kg_relations
                WHERE source_id = :source_id

                UNION ALL

                -- Recursive step
                SELECT
                    r.target_id,
                    p.path_ids || ',' || cast(r.target_id as text),
                    p.path_rels || ',' || cast(r.relation as text),
                    p.depth + 1
                FROM kg_relations r
                JOIN path_search p ON r.source_id = p.last_id
                WHERE p.depth < :max_depth
            )
            SELECT path_ids, path_rels, depth
            FROM path_search
            WHERE last_id = :target_id
            ORDER BY depth ASC
            LIMIT 10
        """)

        result = await session.execute(cte_query, {
            "source_id": source_id,
            "target_id": target_id,
            "max_depth": max_depth
        })

        rows = result.fetchall()

        if not rows:
            return []

        # Collect all unique node IDs to fetch names in bulk
        all_node_ids = set()
        parsed_rows = []
        
        for row in rows:
            # Parse path IDs and relations
            # path_ids is "id1,id2,id3"
            ids = [int(x) for x in row[0].split(',')]
            # path_rels is "rel1,rel2"
            rels = row[1].split(',')

            # Basic cycle check: if IDs are not unique, skip cyclic path
            if len(ids) != len(set(ids)):
                continue

            all_node_ids.update(ids)
            parsed_rows.append((ids, rels))
            
        if not parsed_rows:
            return []

        # Bulk fetch all entity names
        name_stmt = text("SELECT id, name FROM kg_entities WHERE id IN :ids")
        name_stmt = name_stmt.bindparams(bindparam("ids", expanding=True))
        name_res = await session.execute(name_stmt, {"ids": list(all_node_ids)})

        id_to_name = {row.id: row.name for row in name_res}
        
        paths = []
        # Construct result objects
        for ids, rels in parsed_rows:
            # Map IDs to names
            nodes = []
            valid_path = True
            for nid in ids:
                name = id_to_name.get(nid)
                if name is None:
                    # Should not happen if DB is consistent, but handle gracefully
                    valid_path = False
                    break
                nodes.append(name)

            if valid_path:
                paths.append({
                    "nodes": nodes,
                    "relations": rels,
                    "length": len(rels),
                    "confidence": 1.0 - (len(rels) * 0.1)
                })

        return paths
    
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
                # Get reference entity ID
                ref_id_stmt = text("SELECT id FROM kg_entities WHERE name = :name")
                ref_id_res = await session.execute(ref_id_stmt, {"name": entity_name})
                ref_row = ref_id_res.fetchone()
                
                if not ref_row:
                    return []
                ref_id = ref_row[0]
                
                # Get reference entity relation count
                ref_count_stmt = text("SELECT COUNT(*) FROM kg_relations WHERE source_id = :ref_id")
                ref_count_res = await session.execute(ref_count_stmt, {"ref_id": ref_id})
                ref_total = ref_count_res.scalar()
                
                if ref_total == 0:
                    return []

                # Intersection-first optimization using CTEs
                # 1. Identify candidates (entities sharing >=1 relation) -> O(Neighbors)
                # 2. Count totals for candidates only
                # 3. Calculate Jaccard in SQL
                # Note: This query avoids full table scans of unrelated entities.
                stmt = text("""
                    WITH ref_rels AS (
                        SELECT target_id, relation
                        FROM kg_relations
                        WHERE source_id = :ref_id
                    ),
                    candidates AS (
                        SELECT
                            r.source_id,
                            COUNT(r.id) as intersection_cnt
                        FROM kg_relations r
                        JOIN ref_rels rr ON r.target_id = rr.target_id AND r.relation = rr.relation
                        WHERE r.source_id != :ref_id
                        GROUP BY r.source_id
                        HAVING COUNT(r.id) >= :ref_total * :threshold
                    ),
                    candidate_totals AS (
                        SELECT
                            r.source_id,
                            COUNT(r.id) as total_cnt
                        FROM kg_relations r
                        JOIN candidates c ON r.source_id = c.source_id
                        GROUP BY r.source_id
                    )
                    SELECT
                        e.name,
                        c.intersection_cnt,
                        t.total_cnt,
                        (CAST(c.intersection_cnt AS FLOAT) / (t.total_cnt + :ref_total - c.intersection_cnt)) as similarity
                    FROM candidates c
                    JOIN candidate_totals t ON c.source_id = t.source_id
                    JOIN kg_entities e ON c.source_id = e.id
                    WHERE (CAST(c.intersection_cnt AS FLOAT) / (t.total_cnt + :ref_total - c.intersection_cnt)) >= :threshold
                    ORDER BY similarity DESC
                """)

                res = await session.execute(stmt, {
                    "ref_id": ref_id,
                    "ref_total": ref_total,
                    "threshold": similarity_threshold
                })

                for row in res.fetchall():
                    similar_entities.append({
                        "entity": row[0],
                        "similarity": row[3],
                        "shared_relations": row[1]
                    })
                
            return similar_entities
            
        except Exception as e:
            logger.error(f"Similar entity search failed: {e}")
            return []

    async def delete_entity(self, entity_name: str) -> int:
        """
        Delete an entity and all its incident edges.

        Args:
            entity_name: Entity name to delete

        Returns:
            Total count of deleted items (1 entity + N relations)
        """
        try:
            await self.init_db()
            async with self.Session() as session:
                # Find entity ID
                res = await session.execute(text("SELECT id FROM kg_entities WHERE name = :n"), {"n": entity_name})
                row = res.fetchone()
                if not row:
                    return 0

                eid = row[0]

                # Delete relations where source or target is this entity
                stmt = text("DELETE FROM kg_relations WHERE source_id = :eid OR target_id = :eid")
                result = await session.execute(stmt, {"eid": eid})
                deleted_relations = result.rowcount

                # Delete entity
                stmt_ent = text("DELETE FROM kg_entities WHERE id = :eid")
                await session.execute(stmt_ent, {"eid": eid})

                await session.commit()

                total = 1 + deleted_relations
                logger.info(f"Deleted entity '{entity_name}' and {deleted_relations} relations")
                return total

        except Exception as e:
            logger.error(f"Failed to delete entity '{entity_name}': {e}")
            return 0
