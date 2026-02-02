use serde::{Deserialize, Serialize};
use uuid::Uuid;
use anyhow::Result;
use sqlx::{PgPool, Row};

#[derive(Debug, Clone, Serialize, Deserialize)]
pub struct MemoryRecord {
    pub id: Uuid,
    pub embedding: Vec<f32>,
    pub content: String,
    pub confidence: f32,
    pub decay_rate: f32,
    pub source: String,
}

impl MemoryRecord {
    pub fn new(content: String, embedding: Vec<f32>) -> Self {
        Self {
            id: Uuid::new_v4(),
            embedding,
            content,
            confidence: 1.0,
            decay_rate: 0.1,
            source: "node".to_string(),
        }
    }
}

pub struct HiDB {
    pg_pool: PgPool,
    redis_client: redis::Client,
}

impl HiDB {
    pub async fn connect(database_url: &str, redis_url: &str) -> Result<Self> {
        let pg_pool = PgPool::connect(database_url).await?;
        let redis_client = redis::Client::open(redis_url)?;
        
        tracing::info!("HiDB: Connected to PostgreSQL and Redis");
        
        Ok(Self {
            pg_pool,
            redis_client,
        })
    }

    pub async fn store(&self, memory: &MemoryRecord) -> Result<()> {
        // Store in PostgreSQL
        sqlx::query(
            r#"
            INSERT INTO memories (id, embedding, content, confidence, decay_rate, source)
            VALUES ($1, $2, $3, $4, $5, $6)
            "#
        )
        .bind(memory.id)
        .bind(&memory.embedding)
        .bind(&memory.content)
        .bind(memory.confidence)
        .bind(memory.decay_rate)
        .bind(&memory.source)
        .execute(&self.pg_pool)
        .await?;

        // Cache in Redis
        let mut conn = self.redis_client.get_connection()?;
        let key = format!("memory:{}", memory.id);
        let value = serde_json::to_string(memory)?;
        redis::cmd("SET")
            .arg(&key)
            .arg(&value)
            .arg("EX")
            .arg(3600) // 1 hour TTL
            .query::<()>(&mut conn)?;

        Ok(())
    }

    pub async fn semantic_search(&self, query_embedding: &[f32], limit: i64) -> Result<Vec<MemoryRecord>> {
        let rows = sqlx::query(
            r#"
            SELECT id, embedding, content, confidence, decay_rate, source
            FROM memories
            ORDER BY embedding <=> $1
            LIMIT $2
            "#
        )
        .bind(query_embedding)
        .bind(limit)
        .fetch_all(&self.pg_pool)
        .await?;

        let memories = rows.into_iter().map(|row| {
            MemoryRecord {
                id: row.get("id"),
                embedding: row.get("embedding"),
                content: row.get("content"),
                confidence: row.get("confidence"),
                decay_rate: row.get("decay_rate"),
                source: row.get("source"),
            }
        }).collect();

        Ok(memories)
    }

    pub async fn decay_memories(&self) -> Result<()> {
        // Reduce confidence of all memories based on decay_rate
        sqlx::query(
            r#"
            UPDATE memories
            SET confidence = confidence * (1.0 - decay_rate),
                updated_at = NOW()
            WHERE confidence > 0.01
            "#
        )
        .execute(&self.pg_pool)
        .await?;

        // Delete very low confidence memories
        sqlx::query("DELETE FROM memories WHERE confidence < 0.01")
            .execute(&self.pg_pool)
            .await?;

        Ok(())
    }
}

pub async fn init(database_url: &str, redis_url: &str) -> Result<HiDB> {
    HiDB::connect(database_url, redis_url).await
}
