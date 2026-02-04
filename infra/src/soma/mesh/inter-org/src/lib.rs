//! Inter-Org: The Bilingual Transport Layer
//!
//! This library provides a unified interface for sending "Thoughts" via:
//! 1. The Whisper (P2P Mesh) - for local/stealth
//! 2. The Voice (Gateway) - for global/internet (WhatsApp, Signal, etc.)

pub mod protocol;
pub mod router;

pub use router::TransportRouter;
pub use protocol::{TransportType, BilingualMessage};
