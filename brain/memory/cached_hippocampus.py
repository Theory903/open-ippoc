# brain/memory/cached_hippocampus.py
# @cognitive - Enhanced Hippocampus with Vector Caching

from __future__ import annotations

import time
import math
import hashlib
from collections import OrderedDict
from dataclasses import dataclass, field
from typing import List, Dict, Any, Optional, Tuple
from functools import lru_cache

from brain.core.ledger import get_ledger
from brain.core.orchestrator import get_orchestrator
from .consolidation import MemoryEntry, Hippocampus


@dataclass
class CachedVector:
    """Cached vector representation with metadata"""
    vector_hash: str
    embedding: List[float]
    content_hash: str
    accessed_at: float
    access_count: int = 1
    ttl: float = 3600.0  # 1 hour default TTL


class LRUCache:
    """LRU Cache implementation for vector embeddings"""
    
    def __init__(self, maxsize: int = 10000):
        self.maxsize = maxsize
        self.cache = OrderedDict()
        
    def get(self, key: str) -> Optional[Any]:
        if key not in self.cache:
            return None
        # Move to end (most recently used)
        self.cache.move_to_end(key)
        return self.cache[key]
    
    def put(self, key: str, value: Any) -> None:
        if key in self.cache:
            self.cache.move_to_end(key)
        self.cache[key] = value
        if len(self.cache) > self.maxsize:
            # Remove least recently used
            self.cache.popitem(last=False)
    
    def invalidate(self, key: str) -> bool:
        if key in self.cache:
            del self.cache[key]
            return True
        return False
    
    def size(self) -> int:
        return len(self.cache)
    
    def clear(self) -> None:
        self.cache.clear()


class CachedHippocampus(Hippocampus):
    """
    Enhanced Hippocampus with vector caching, compression, and performance optimizations.
    
    Features:
    - LRU vector embedding cache
    - Content-based deduplication
    - Adaptive TTL based on access patterns
    - Compression for frequently accessed vectors
    - Batch operations for improved throughput
    """
    
    def __init__(self, vector_cache_size: int = 10000, enable_compression: bool = True) -> None:
        super().__init__()
        self.vector_cache = LRUCache(maxsize=vector_cache_size)
        self.content_cache = {}  # content_hash -> memory_id mapping
        self.enable_compression = enable_compression
        self.stats = {
            'cache_hits': 0,
            'cache_misses': 0,
            'deduped_entries': 0,
            'compressed_vectors': 0,
            'total_accesses': 0
        }
        
    def _compute_content_hash(self, content: str) -> str:
        """Compute deterministic hash for content deduplication"""
        return hashlib.sha256(content.encode('utf-8')).hexdigest()
    
    def _compute_vector_hash(self, embedding: List[float]) -> str:
        """Compute hash for vector embedding"""
        # Convert floats to string with fixed precision for consistent hashing
        vector_str = ','.join(f"{x:.6f}" for x in embedding)
        return hashlib.md5(vector_str.encode('utf-8')).hexdigest()
    
    async def add_memory(self, content: str, importance: float = 0.5, 
                        mem_type: str = "episodic", embedding: Optional[List[float]] = None) -> MemoryEntry:
        """Enhanced memory addition with caching and deduplication"""
        
        # Check for content deduplication
        content_hash = self._compute_content_hash(content)
        if content_hash in self.content_cache:
            existing_id = self.content_cache[content_hash]
            # Update existing entry instead of creating new one
            entry = self.memories.get(existing_id)
            if entry:
                entry.last_accessed = time.time()
                entry.access_count += 1
                entry.importance = min(entry.importance + 0.05, 1.0)  # Smaller boost for duplicates
                self.stats['deduped_entries'] += 1
                return entry
        
        # Create new memory entry
        import uuid
        mem_id = str(uuid.uuid4())
        entry = MemoryEntry(
            memory_id=mem_id,
            content=content,
            created_at=time.time(),
            last_accessed=time.time(),
            importance=importance,
            memory_type=mem_type
        )
        
        self.memories[mem_id] = entry
        self.content_cache[content_hash] = mem_id
        
        # Cache vector embedding if provided
        if embedding:
            await self._cache_vector_embedding(content, embedding, mem_type)
        
        return entry
    
    async def _cache_vector_embedding(self, content: str, embedding: List[float], 
                                    mem_type: str) -> None:
        """Cache vector embedding with adaptive TTL"""
        content_hash = self._compute_content_hash(content)
        vector_hash = self._compute_vector_hash(embedding)
        
        # Adaptive TTL based on memory type and importance
        base_ttl = 3600.0  # 1 hour
        if mem_type == "semantic":
            base_ttl *= 2  # Semantic memories last longer
        if hasattr(self.memories.get(content_hash, None), 'importance'):
            importance = self.memories[content_hash].importance
            base_ttl *= (1 + importance)  # Higher importance = longer TTL
            
        cached_vector = CachedVector(
            vector_hash=vector_hash,
            embedding=embedding,
            content_hash=content_hash,
            accessed_at=time.time(),
            ttl=base_ttl
        )
        
        self.vector_cache.put(vector_hash, cached_vector)
        
        # Optional compression for frequently accessed vectors
        if self.enable_compression and cached_vector.access_count > 10:
            await self._compress_vector(cached_vector)
    
    async def _compress_vector(self, vector: CachedVector) -> None:
        """Compress vector embedding for storage efficiency"""
        # Simple quantization compression - reduce precision for frequently accessed vectors
        if len(vector.embedding) > 0:
            compressed = [round(x, 4) for x in vector.embedding]  # 4 decimal places instead of 6
            vector.embedding = compressed
            self.stats['compressed_vectors'] += 1
    
    async def access_memory(self, memory_id: str) -> Optional[MemoryEntry]:
        """Enhanced memory access with caching statistics"""
        self.stats['total_accesses'] += 1
        entry = self.memories.get(memory_id)
        
        if entry:
            entry.last_accessed = time.time()
            entry.access_count += 1
            # Boost importance on access
            entry.importance = min(entry.importance + 0.1, 1.0)
            
            # Update cached vector access
            content_hash = self._compute_content_hash(entry.content)
            # This would trigger vector cache refresh in a real implementation
            
        return entry
    
    async def search_similar(self, query_embedding: List[float], 
                           k: int = 10, threshold: float = 0.7) -> List[Tuple[MemoryEntry, float]]:
        """Enhanced similarity search with cached vectors"""
        results = []
        
        # Check vector cache first
        query_hash = self._compute_vector_hash(query_embedding)
        cached_result = self.vector_cache.get(query_hash)
        
        if cached_result:
            self.stats['cache_hits'] += 1
            # Return cached similar memories
            return await self._get_cached_similarities(query_embedding, k, threshold)
        else:
            self.stats['cache_misses'] += 1
            # Perform full search and cache results
            return await self._perform_full_similarity_search(query_embedding, k, threshold)
    
    async def _get_cached_similarities(self, query_embedding: List[float], 
                                     k: int, threshold: float) -> List[Tuple[MemoryEntry, float]]:
        """Retrieve similarities from cache"""
        # In a real implementation, this would use cached ANN results
        # For now, simulate with basic cosine similarity on cached vectors
        similarities = []
        
        for vector_hash, cached_vector in list(self.vector_cache.cache.items()):
            if time.time() - cached_vector.accessed_at > cached_vector.ttl:
                self.vector_cache.invalidate(vector_hash)
                continue
                
            # Compute similarity (simplified)
            similarity = self._cosine_similarity(query_embedding, cached_vector.embedding)
            if similarity >= threshold:
                # Find corresponding memory entry
                for entry in self.memories.values():
                    if self._compute_content_hash(entry.content) == cached_vector.content_hash:
                        similarities.append((entry, similarity))
                        break
        
        # Sort by similarity and return top k
        similarities.sort(key=lambda x: x[1], reverse=True)
        return similarities[:k]
    
    async def _perform_full_similarity_search(self, query_embedding: List[float], 
                                            k: int, threshold: float) -> List[Tuple[MemoryEntry, float]]:
        """Perform full similarity search and cache results"""
        # In a real implementation, this would use vector database
        # For now, simulate with basic cosine similarity
        similarities = []
        
        for entry in self.memories.values():
            # Generate embedding if not cached (simplified)
            content_hash = self._compute_content_hash(entry.content)
            cached_vector = None
            
            # Look for cached vector
            for vector_hash, vec in self.vector_cache.cache.items():
                if vec.content_hash == content_hash:
                    cached_vector = vec
                    break
            
            if cached_vector:
                similarity = self._cosine_similarity(query_embedding, cached_vector.embedding)
            else:
                # Simulate embedding generation
                similarity = self._similarity_heuristic(query_embedding, entry.content)
            
            if similarity >= threshold:
                similarities.append((entry, similarity))
        
        # Sort and cache top results
        similarities.sort(key=lambda x: x[1], reverse=True)
        top_results = similarities[:k]
        
        # Cache the query result
        query_hash = self._compute_vector_hash(query_embedding)
        # In real implementation, cache the ANN search results
        
        return top_results
    
    def _cosine_similarity(self, a: List[float], b: List[float]) -> float:
        """Compute cosine similarity between two vectors"""
        if len(a) != len(b) or len(a) == 0:
            return 0.0
        
        dot_product = sum(x * y for x, y in zip(a, b))
        magnitude_a = math.sqrt(sum(x * x for x in a))
        magnitude_b = math.sqrt(sum(y * y for y in b))
        
        if magnitude_a == 0 or magnitude_b == 0:
            return 0.0
            
        return dot_product / (magnitude_a * magnitude_b)
    
    def _similarity_heuristic(self, query_embedding: List[float], content: str) -> float:
        """Heuristic similarity for demonstration purposes"""
        # Simple keyword matching heuristic
        query_length = len(query_embedding)
        content_length = len(content.split())
        
        # Normalize based on length difference
        length_ratio = min(query_length, content_length) / max(query_length, content_length)
        
        # Content overlap heuristic
        common_words = len(set(str(query_embedding)[:50].lower().split()) & 
                          set(content.lower().split()))
        overlap_score = common_words / max(len(content.split()), 1)
        
        return (length_ratio + overlap_score) / 2
    
    async def batch_add_memories(self, memories: List[Dict[str, Any]]) -> List[MemoryEntry]:
        """Batch add memories for improved performance"""
        results = []
        
        for mem_data in memories:
            entry = await self.add_memory(
                content=mem_data['content'],
                importance=mem_data.get('importance', 0.5),
                mem_type=mem_data.get('mem_type', 'episodic'),
                embedding=mem_data.get('embedding')
            )
            results.append(entry)
        
        return results
    
    async def get_cache_statistics(self) -> Dict[str, Any]:
        """Get detailed cache performance statistics"""
        total_requests = self.stats['cache_hits'] + self.stats['cache_misses']
        hit_rate = self.stats['cache_hits'] / max(total_requests, 1)
        
        return {
            'cache_hits': self.stats['cache_hits'],
            'cache_misses': self.stats['cache_misses'],
            'hit_rate': hit_rate,
            'deduped_entries': self.stats['deduped_entries'],
            'compressed_vectors': self.stats['compressed_vectors'],
            'total_accesses': self.stats['total_accesses'],
            'vector_cache_size': self.vector_cache.size(),
            'content_cache_size': len(self.content_cache),
            'memory_entries': len(self.memories)
        }
    
    async def cleanup_expired_cache(self) -> int:
        """Remove expired cached vectors"""
        current_time = time.time()
        expired_count = 0
        
        expired_keys = []
        for vector_hash, cached_vector in self.vector_cache.cache.items():
            if current_time - cached_vector.accessed_at > cached_vector.ttl:
                expired_keys.append(vector_hash)
        
        for key in expired_keys:
            self.vector_cache.invalidate(key)
            expired_count += 1
            
        return expired_count


# Singleton instance
_cached_hippocampus_instance: CachedHippocampus | None = None


def get_cached_hippocampus(vector_cache_size: int = 10000, 
                          enable_compression: bool = True) -> CachedHippocampus:
    """Get singleton instance of CachedHippocampus"""
    global _cached_hippocampus_instance
    if _cached_hippocampus_instance is None:
        _cached_hippocampus_instance = CachedHippocampus(
            vector_cache_size=vector_cache_size,
            enable_compression=enable_compression
        )
    return _cached_hippocampus_instance