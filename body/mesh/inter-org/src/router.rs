use anyhow::{Result, anyhow};
use tracing::info;
use crate::protocol::{BilingualMessage, TransportType};

pub struct TransportRouter {
    // mesh_client: Arc<ai_mesh::Client>,
    // gateway_client: Arc<GatewayClient>,
}

impl TransportRouter {
    pub fn new() -> Self {
        Self {
            // Initialize clients
        }
    }

    pub async fn route(&self, msg: BilingualMessage) -> Result<()> {
        match msg.transport_preference {
            TransportType::Mesh => self.send_mesh(msg).await,
            TransportType::Gateway => self.send_gateway(msg).await,
            TransportType::Broadcast => {
                let mesh_res = self.send_mesh(msg.clone()).await;
                let gate_res = self.send_gateway(msg).await;
                
                if mesh_res.is_err() && gate_res.is_err() {
                    return Err(anyhow!("Both transports failed"));
                }
                Ok(())
            }
        }
    }

    async fn send_mesh(&self, msg: BilingualMessage) -> Result<()> {
        info!("🤫 [Whisper] Sending via AI-Mesh to {:?}...", msg.target_id);
        // crate::ai_mesh::send(...)
        Ok(())
    }

    async fn send_gateway(&self, _msg: BilingualMessage) -> Result<()> {
        info!("🗣️ [Voice] Sending via OpenClaw Gateway (WhatsApp/Signal)...");
        // Serialize to Base64 blob and send as "file attachment" logic would go here
        info!("   Payload: [ENCRYPTED_BLOB] -> +15550199");
        Ok(())
    }
}
