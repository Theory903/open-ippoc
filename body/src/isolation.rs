use anyhow::{Result, Context};
use std::path::{Path, PathBuf};
use std::fs;
use tracing::info;

pub struct NodeIsolation {
    pub root_dir: PathBuf,
}

impl NodeIsolation {
    pub fn init(node_id: &str) -> Result<Self> {
        // Canonical Root: /tmp/ippoc/nodes/<node_id> (Using /tmp for portability in this environment, normally /var/lib/ippoc)
        let base_dir = std::env::var("IPPOC_DATA_DIR")
            .unwrap_or_else(|_| "/tmp/ippoc".to_string());
        
        let root_dir = Path::new(&base_dir).join("nodes").join(node_id);
        
        info!("NodeIsolation: Initializing sovereign boundaries at {:?}", root_dir);

        // Required Subdirectories
        let subdirs = ["data", "memory", "sandbox", "logs", "tmp"];
        
        for subdir in &subdirs {
            let path = root_dir.join(subdir);
            fs::create_dir_all(&path)
                .with_context(|| format!("Failed to create isolation directory: {:?}", path))?;
        }

        // Rule 2.3: Physical Isolation Law - Verify absolute path usage
        if !root_dir.is_absolute() {
             anyhow::bail!("Isolation root must be an absolute path: {:?}", root_dir);
        }

        Ok(Self { root_dir })
    }

    #[allow(dead_code)]
    pub fn data_path(&self) -> PathBuf { self.root_dir.join("data") }
    #[allow(dead_code)]
    pub fn memory_path(&self) -> PathBuf { self.root_dir.join("memory") }
    pub fn sandbox_path(&self) -> PathBuf { self.root_dir.join("sandbox") }
    #[allow(dead_code)]
    pub fn logs_path(&self) -> PathBuf { self.root_dir.join("logs") }
    #[allow(dead_code)]
    pub fn tmp_path(&self) -> PathBuf { self.root_dir.join("tmp") }
}
