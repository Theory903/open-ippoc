use serde::{Deserialize, Serialize};
use uuid::Uuid;
use anyhow::Result;
use sqlx::{any::AnyPool, Row};

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
    pool: AnyPool,
    redis_client: Option<redis::Client>,
}

impl HiDB {
    pub async fn connect(database_url: &str, redis_url: Option<&str>) -> Result<Self> {
        sqlx::any::install_default_drivers();
        let pool = AnyPool::connect(database_url).await?;
        
        let redis_client = if let Some(url) = redis_url {
            if url.is_empty() {
                None
            } else {
                match redis::Client::open(url) {
                    Ok(client) => Some(client),
                    Err(_) => None,
                }
            }
        } else {
            None
        };
        
        tracing::info!("HiDB: Connected to {} (Redis: {})", 
            if database_url.starts_with("postgres") { "PostgreSQL" } else { "SQLite" },
            if redis_client.is_some() { "Active" } else { "Inactive" }
        );
        
        Ok(Self {
            pool,
            redis_client,
        })
    }

    pub async fn store(&self, memory: &MemoryRecord) -> Result<()> {
        let is_postgres = self.pool.connect_options().database_name().map(|name| name == "postgres").unwrap_or(false);
        
        let query = if is_postgres {
            r#"INSERT INTO memories (id, embedding, content, confidence, decay_rate, source) VALUES ($1, $2, $3, $4, $5, $6)"#
        } else {
            r#"INSERT INTO memories (id, embedding, content, confidence, decay_rate, source) VALUES (?, ?, ?, ?, ?, ?)"#
        };

        sqlx::query(query)
            .bind(memory.id)
            .bind(&memory.embedding)
            .bind(&memory.content)
            .bind(memory.confidence)
            .bind(memory.decay_rate)
            .bind(&memory.source)
            .execute(&self.pool)
            .await?;

        if let Some(ref client) = self.redis_client {
            if let Ok(mut conn) = client.get_connection() {
                let key = format!("memory:{}", memory.id);
                if let Ok(value) = serde_json::to_string(memory) {
                    let _: () = redis::cmd("SET").arg(&key).arg(&value).arg("EX").arg(3600).query(&mut conn).unwrap_or(());
                }
            }
        }

        Ok(())
    }

    pub async fn semantic_search(&self, query_embedding: &[f32], limit: i64) -> Result<Vec<MemoryRecord>> {
        // Fallback for AnyPool vector search (requires pgvector vs sqlite simple)
        // For now, we use a basic ORDER BY if not postgres
        let is_postgres = self.pool.connect_options().database_name().map(|name| name == "postgres").unwrap_or(false);
        
        let rows = if is_postgres {
            sqlx::query(r#"SELECT id, embedding, content, confidence, decay_rate, source FROM memories ORDER BY embedding <=> $1 LIMIT $2"#)
                .bind(query_embedding)
                .bind(limit)
                .fetch_all(&self.pool)
                .await?
        } else {
            sqlx::query(r#"SELECT id, embedding, content, confidence, decay_rate, source FROM memories LIMIT ?"#)
                .bind(limit)
                .fetch_all(&self.pool)
                .await?
        };

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

    pub async fn get_recent(&self, limit: i64) -> Result<Vec<MemoryRecord>> {
        let is_postgres = self.pool.connect_options().database_name().map(|name| name == "postgres").unwrap_or(false);
        let query = if is_postgres {
            "SELECT id, embedding, content, confidence, decay_rate, source FROM memories ORDER BY created_at DESC LIMIT $1"
        } else {
            "SELECT id, embedding, content, confidence, decay_rate, source FROM memories ORDER BY created_at DESC LIMIT ?"
        };

        let rows = sqlx::query(query)
            .bind(limit)
            .fetch_all(&self.pool)
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
        sqlx::query("UPDATE memories SET confidence = confidence * (1.0 - decay_rate) WHERE confidence > 0.01")
            .execute(&self.pool)
            .await?;
        sqlx::query("DELETE FROM memories WHERE confidence < 0.01")
            .execute(&self.pool)
            .await?;
        Ok(())
    }
}

pub async fn init(database_url: &str, redis_url: &str) -> Result<HiDB> {
    HiDB::connect(database_url, if redis_url.is_empty() { None } else { Some(redis_url) }).await
}
