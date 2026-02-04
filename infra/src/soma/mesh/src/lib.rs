//! AI Mesh - Secure P2P Communication for IPPOC-OS Nodes
//!
//! Provides encrypted, authenticated communication between AI nodes
//! using X25519 key exchange and AES-256-GCM encryption (inspired by BitChat).

mod crypto;
mod messages;
mod peer;
mod mesh;
pub mod identity;
pub mod transport;

pub use crypto::{NodeIdentity, SharedSecret, encrypt_message, decrypt_message};
pub use messages::{AiMessage, MessageType, Thought, Broadcast};
pub use peer::{Peer, PeerStatus};
pub use mesh::{AiMesh, MeshConfig};

/// Re-export common types
pub mod prelude {
    pub use crate::{AiMesh, MeshConfig, AiMessage, MessageType, Peer, NodeIdentity};
}
pub mod economy;
pub mod lifecycle;
