use anyhow::Result;
// use async_trait::async_trait;
use tracing::info;
use serde::{Deserialize, Serialize};

#[derive(Debug, Serialize, Deserialize)]
pub struct ThoughtRequest {
    pub query: String,
    pub context_history: Vec<String>,
}

#[derive(Debug, Serialize, Deserialize)]
pub struct ThoughtResponse {
    pub answer: String,
    pub confidence: f32,
    pub sources: Vec<String>,
}

use hidb::HiDB;
use std::sync::Arc;

/// The Thinking Engine
pub struct Cerebrum {
    search: SearchLobe,
    memories: MemoryLobe,
}

impl Cerebrum {
    pub fn new(hidb: Arc<HiDB>) -> Self {
        Self {
            search: SearchLobe::new(),
            memories: MemoryLobe::new(hidb),
        }
    }

    pub async fn think(&self, req: ThoughtRequest) -> Result<ThoughtResponse> {
        info!("Cerebrum thinking about: {}", req.query);

        // 1. Quick Reflex (Do I know this?)
        let memory_strings = self.memories.recall(&req.query).await.unwrap_or_default();
        let memory_context = if !memory_strings.is_empty() {
            format!("I recall: {}\n\n", memory_strings.join("\n"))
        } else {
            String::new()
        };

        // 2. Information Retrieval (Search)
        let search_results = self.search.search(&req.query).await.unwrap_or_default();

        // 3. Synthesis (LLM Call - Simulated for now, or use OpenRouter via env?)
        // For this step, we'll confirm we *found* info.
        
        // TODO: In real implementation, this calls the local LLM or OpenAI with the context.
        // For the "I am weak" fix, we'll make it return a grounded simulation.
        
        let answer = if search_results.is_empty() {
            format!("{}I pondered '{}' but found no external info, and my internal weights are uncertain.", memory_context, req.query)
        } else {
            format!(
                "{}Based on my research ({})\n{}\n\nSource: {}", 
                memory_context,
                search_results[0].title,
                search_results[0].snippet, 
                search_results[0].url
            )
        };

        // 4. Memorize this interaction (Hippocampal consolidation)
        // We store the query + answer as a memory trace
        // In real system, this happens async or in background
        if let Err(e) = self.memories.memorize(&req.query, &answer).await {
            tracing::warn!("Failed to consolidate memory: {}", e);
        }

        Ok(ThoughtResponse {
            answer,
            confidence: 0.8,
            sources: search_results.into_iter().map(|r| r.url).collect(),
        })
    }
}

// --- Lobes ---

struct MemoryLobe {
    hidb: Arc<HiDB>,
    _embedding_client: reqwest::Client,
}

impl MemoryLobe {
    pub fn new(hidb: Arc<HiDB>) -> Self {
        Self {
            hidb,
            _embedding_client: reqwest::Client::new(),
        }
    }

    pub async fn recall(&self, query: &str) -> Result<Vec<String>> {
        info!("Recalling memories related to: {}", query);
        // 1. Generate Embedding (Mock for now, or call Sidecar)
        // In a real implementation: call local LLM sidecar /v1/embeddings
        let mock_embedding = vec![0.0f32; 1536]; // Placeholder 1536 dim
        
        // 2. Query HiDB
        let memories = self.hidb.semantic_search(&mock_embedding, 3).await?;
        
        // 3. Format
        let results = memories.into_iter()
            .map(|m| format!("Memory (conf: {:.2}): {}", m.confidence, m.content))
            .collect();
            
        Ok(results)
    }

    pub async fn memorize(&self, query: &str, answer: &str) -> Result<()> {
        use hidb::MemoryRecord;
        
        info!("Consolidating memory: '{}' -> ...", query);
        
        // 1. Create content blob
        let content = format!("Q: {}\nA: {}", query, answer);
        
        // 2. Generate Embedding (Mock)
        // Ideally we embed the Question or Q+A
        let mock_embedding = vec![0.0f32; 1536]; 

        // 3. Store
        let record = MemoryRecord::new(content, mock_embedding);
        self.hidb.store(&record).await?;
        
        Ok(())
    }
}

struct SearchLobe {
    client: reqwest::Client,
}

#[derive(Debug, Deserialize)]
struct SearchResult {
    title: String,
    url: String,
    snippet: String,
}

impl SearchLobe {
    pub fn new() -> Self {
        Self {
            client: reqwest::Client::new(),
        }
    }

    pub async fn search(&self, query: &str) -> Result<Vec<SearchResult>> {
        // Real logic: If query is a URL, fetch it. If not, do a mock search for now (or Bing API if env set)
        
        if query.starts_with("http") {
             let res = self.client.get(query).send().await?;
             let title = query.to_string(); // In real app, parse HTML <title>
             let snippet = format!("TITLE: {}\nFetched content from {}: Status {}", title, query, res.status());
             
             return Ok(vec![SearchResult {
                 title,
                 url: query.to_string(),
                 snippet,
             }]);
        }
        
        // Mock for stability unless we have an endpoint
        if query.to_lowercase().contains("ippoc") {
            return Ok(vec![SearchResult {
                title: "IPPOC-OS Documentation".to_string(),
                url: "https://github.com/ippoc/ippoc".to_string(),
                snippet: "IPPOC-OS is a biological-inspired AI kernel combining Rust performance with Agentic workflows.".to_string()
            }]);
        }
        
        Ok(vec![])
    }
}
