use anyhow::{Context, Result};
use std::process::Stdio;
use tokio::process::{Child, Command};
use tracing::info;

#[allow(dead_code)]
pub struct VllmSidecar {
    process: Option<Child>,
    port: u16,
}

#[allow(dead_code)]
impl VllmSidecar {
    pub fn new(port: u16) -> Self {
        Self { process: None, port }
    }

    pub async fn start(&mut self) -> Result<()> {
        info!("Starting vLLM Sidecar on port {}...", self.port);
        
        let script_path = "./scripts/vllm_service.sh";
        
        let child = Command::new("bash")
            .arg(script_path)
            .arg(self.port.to_string())
            .stdout(Stdio::piped())
            .stderr(Stdio::piped())
            .spawn()
            .context("Failed to spawn vLLM sidecar")?;
            
        self.process = Some(child);
        info!("vLLM Sidecar spawned successfully.");
        Ok(())
    }

    pub async fn health_check(&self) -> bool {
        let url = format!("http://localhost:{}/v1/models", self.port);
        match reqwest::get(&url).await {
            Ok(resp) => resp.status().is_success(),
            Err(_) => false,
        }
    }
}

impl Drop for VllmSidecar {
    fn drop(&mut self) {
        if let Some(mut child) = self.process.take() {
            info!("Killing vLLM Sidecar...");
            let _ = child.start_kill();
        }
    }
}
