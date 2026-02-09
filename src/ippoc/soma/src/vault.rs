use serde::{Deserialize, Serialize};
use std::collections::HashMap;
use std::path::{Path, PathBuf};
use std::sync::Arc;
use tokio::sync::RwLock;
use anyhow::Result;

#[derive(Debug, Clone, Serialize, Deserialize, Default)]
pub struct VaultData {
    pub tokens: HashMap<String, String>,
}

#[derive(Debug)]
pub struct SovereignVault {
    storage_path: PathBuf,
    data: Arc<RwLock<VaultData>>,
}

impl SovereignVault {
    pub fn new(storage_root: &Path) -> Result<Self> {
        let vault_dir = storage_root.join("vault");
        std::fs::create_dir_all(&vault_dir)?;
        
        let storage_path = vault_dir.join("secrets.json");
        let data = if storage_path.exists() {
            let content = std::fs::read_to_string(&storage_path)?;
            serde_json::from_str(&content).unwrap_or_default()
        } else {
            VaultData::default()
        };

        Ok(Self {
            storage_path,
            data: Arc::new(RwLock::new(data)),
        })
    }

    pub async fn get_token(&self, scope: &str) -> Option<String> {
        let data = self.data.read().await;
        data.tokens.get(scope).cloned()
    }

    pub async fn set_token(&self, scope: String, token: String) -> Result<()> {
        {
            let mut data = self.data.write().await;
            data.tokens.insert(scope, token);
        }
        self.save().await
    }

    async fn save(&self) -> Result<()> {
        let data = self.data.read().await;
        let content = serde_json::to_string_pretty(&*data)?;
        tokio::fs::write(&self.storage_path, content).await?;
        Ok(())
    }

    pub async fn get_all_tokens(&self, scopes: &[String]) -> HashMap<String, String> {
        let data = self.data.read().await;
        let mut results = HashMap::new();
        for scope in scopes {
            if let Some(token) = data.tokens.get(scope) {
                results.insert(scope.clone(), token.clone());
            }
        }
        results
    }
}
