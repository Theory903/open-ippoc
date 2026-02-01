# ARCHITECTURE: Cognitive Storage Layer

**COMPONENT:** Memory / Storage
**TYPE:** Hybrid Polyglot Persistence

---

## 1. Core Concept
**"One Logical Memory → Multiple Physical Representations"**

Instead of relying on a single database (e.g., just Postgres or just Pinecone), we define a **Cognitive Storage Layer** that manages data consistency across specialized engines.

---

## 2. The Unified Memory Record (Logical Schema)

This is the single source of truth object passed within the system.

```typescript
struct MemoryRecord {
    id: UUID;
    owner_id: UUID;
    type: MemoryType; // Episodic, Semantic, Procedural
    
    // Content
    raw_content: String;
    crux: String; // Summarized core meaning
    
    // Neural Representations
    embedding: Vector<Reals>;
    user_embedding_snapshot: Vector<Reals>; // Context at creation time
    
    // Meta-Cognitive Metadata
    confidence: Float;
    salience: Float;
    decay_rate: Float; // Predicted survivability
    
    // Graph Connections
    graph_edges: List<Edge>;
    
    // Lifecycle
    access_stats: AccessMetrics;
    version_chain: List<VersionID>;
    flags: Set<Flags>;
}
```

---

## 3. Physical Storage Architecture (The Stack)

| Function | Technology | Role |
| :--- | :--- | :--- |
| **Source of Truth** | **PostgreSQL** | ACID transactions, Audits, Rollbacks, Consistency. |
| **Vector Search** | **pgvector** | Dense retrieval. Kept in-house (same DB as truth) for consistency. |
| **Graph Relations** | **PostgreSQL** | Adjacency lists + Materialized Views for recursive queries. |
| **Fast Cache** | **Redis** | Hot memory access, ephemeral buffers. |
| **Decay Engine** | **Background Workers** | Offline processes that prune/archive memories based on `P(survival)`. |

**Design Policy:** No external vendor lock-in for core memory.

---

## 4. Cognitive Indexes (Learned Indexing)

Querying is not just by `ID` or `KNN`. We maintain specialized indexes:

1.  **Semantic Cluster Index:** pre-grouped memories by topic.
2.  **User Similarity Index:** memories close to the current `user_embedding`.
3.  **Confidence Band Index:** fast retrieval of "high certainty" facts.
4.  **Temporal Relevance Index:** time-decayed access paths.

These indexes are updated asynchronously (Offline Training Loop).
