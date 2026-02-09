# HiDB Configuration

## Environment Variables

```bash
# PostgreSQL
DATABASE_URL=postgresql://user:password@localhost:5432/ippoc_hidb

# Redis
REDIS_URL=redis://localhost:6379
```

## Setup

### 1. Start PostgreSQL with pgvector

```bash
docker run -d \
  --name ippoc-postgres \
  -e POSTGRES_PASSWORD=ippoc_secret \
  -e POSTGRES_DB=ippoc_hidb \
  -p 5432:5432 \
  pgvector/pgvector:pg16
```

### 2. Run Migrations

```bash
psql $DATABASE_URL -f libs/hidb/migrations/001_init.sql
```

### 3. Start Redis

```bash
docker run -d \
  --name ippoc-redis \
  -p 6379:6379 \
  redis:7-alpine
```

## Usage

```rust
let hidb = hidb::init(&database_url, &redis_url).await?;

// Store a memory
let memory = MemoryRecord::new(
    "The capital of France is Paris".to_string(),
    vec![0.1, 0.2, ...] // embedding
);
hidb.store(&memory).await?;

// Semantic search
let results = hidb.semantic_search(&query_embedding, 10).await?;
```
