use serde::{Serialize, Deserialize};
use uuid::Uuid;

#[derive(Debug, Clone, Serialize, Deserialize)]
pub enum TransportType {
    Mesh,       // Local P2P
    Gateway,    // Internet (WhatsApp/Discord)
    Broadcast,  // Both
}

#[derive(Debug, Clone, Serialize, Deserialize)]
pub struct BilingualMessage {
    pub id: Uuid,
    pub sender_id: Uuid,
    pub target_id: Option<Uuid>, // None = Broadcast
    pub content: String,
    pub transport_preference: TransportType,
    pub signature: String, // Integrity check
}

impl BilingualMessage {
    pub fn new(sender: Uuid, content: String, transport: TransportType) -> Self {
        Self {
            id: Uuid::new_v4(),
            sender_id: sender,
            target_id: None,
            content,
            transport_preference: transport,
            signature: String::new(), // To be signed
        }
    }

    pub fn with_target(mut self, target: Uuid) -> Self {
        self.target_id = Some(target);
        self
    }
}
