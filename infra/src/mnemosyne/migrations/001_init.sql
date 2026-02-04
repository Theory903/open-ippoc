-- HiDB Cognitive Memory Schema
-- PostgreSQL with pgvector extension

CREATE EXTENSION IF NOT EXISTS vector;
CREATE EXTENSION IF NOT EXISTS "uuid-ossp";

-- Main memories table
CREATE TABLE memories (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    embedding vector(768),  -- Assuming 768-dim embeddings (adjust as needed)
    content TEXT NOT NULL,
    confidence REAL DEFAULT 1.0,
    decay_rate REAL DEFAULT 0.1,
    source TEXT NOT NULL,
    created_at TIMESTAMP DEFAULT NOW(),
    updated_at TIMESTAMP DEFAULT NOW()
);

-- Index for vector similarity search
CREATE INDEX memories_embedding_idx ON memories 
USING ivfflat (embedding vector_cosine_ops)
WITH (lists = 100);

-- Index for source filtering
CREATE INDEX memories_source_idx ON memories(source);

-- Causal links between memories
CREATE TABLE causal_links (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    from_memory_id UUID REFERENCES memories(id) ON DELETE CASCADE,
    to_memory_id UUID REFERENCES memories(id) ON DELETE CASCADE,
    strength REAL DEFAULT 1.0,
    created_at TIMESTAMP DEFAULT NOW()
);

-- Index for graph traversal
CREATE INDEX causal_links_from_idx ON causal_links(from_memory_id);
CREATE INDEX causal_links_to_idx ON causal_links(to_memory_id);
