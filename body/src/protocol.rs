use serde::{Serialize, Deserialize};
use anyhow::Result;
use tracing::{info, warn};
use std::time::{SystemTime, UNIX_EPOCH};
use std::collections::HashMap;
use std::sync::Mutex;
use ed25519_dalek::{SigningKey, Signature, Signer, Verifier, VerifyingKey};

#[derive(Serialize, Deserialize, Debug, Clone)]
pub struct SignedPacket {
    pub header: PacketHeader,
    pub payload: Vec<u8>,
}

#[derive(Serialize, Deserialize, Debug, Clone)]
pub struct PacketHeader {
    pub node_id: String,
    pub signature: Vec<u8>, // Binary Ed25519 Signature
    pub timestamp: u64,
    pub nonce: String,
}

impl SignedPacket {
    #[allow(dead_code)]
    pub fn sign(node_id: &str, signing_key: &SigningKey, payload: Vec<u8>) -> Result<Self> {
        let timestamp = SystemTime::now()
            .duration_since(UNIX_EPOCH)?
            .as_secs();
        
        let nonce = uuid::Uuid::new_v4().to_string();
        
        // Canonical material for signature: Payload || Timestamp || Nonce
        let mut material = Vec::new();
        material.extend_from_slice(&payload);
        material.extend_from_slice(&timestamp.to_be_bytes());
        material.extend_from_slice(nonce.as_bytes());
        
        let signature = signing_key.sign(&material).to_bytes().to_vec();

        Ok(Self {
            header: PacketHeader {
                node_id: node_id.to_string(),
                signature,
                timestamp,
                nonce,
            },
            payload,
        })
    }

    #[allow(dead_code)]
    pub fn verify(&self, public_key_bytes: &[u8]) -> Result<bool> {
        // 1. Verify Timestamp (Anti-Replay Window: 5 minutes)
        let now = SystemTime::now()
            .duration_since(UNIX_EPOCH)?
            .as_secs();
            
        if self.header.timestamp < now - 300 || self.header.timestamp > now + 300 {
            warn!("Protocol: Signature REJECTED. Packet timestamp out of valid window.");
            return Ok(false);
        }

        // 2. Ed25519 Verification
        let verifying_key = VerifyingKey::from_bytes(public_key_bytes.try_into()?)?;
        let signature = Signature::from_slice(&self.header.signature)?;
        
        let mut material = Vec::new();
        material.extend_from_slice(&self.payload);
        material.extend_from_slice(&self.header.timestamp.to_be_bytes());
        material.extend_from_slice(self.header.nonce.as_bytes());

        if let Err(_) = verifying_key.verify(&material, &signature) {
             warn!("Protocol: Signature MISMATCH for packet from {}", self.header.node_id);
             return Ok(false);
        }

        info!("Protocol: Packet verified successfully from {}", self.header.node_id);
        Ok(true)
    }
}

#[allow(dead_code)]
pub struct ReplayCache {
    seen_nonces: Mutex<HashMap<String, u64>>, // Nonce -> Timestamp
}

impl ReplayCache {
    pub fn new() -> Self {
        Self { seen_nonces: Mutex::new(HashMap::new()) }
    }

    pub fn is_replay(&self, nonce: &str) -> bool {
        let now = SystemTime::now()
            .duration_since(UNIX_EPOCH)
            .unwrap()
            .as_secs();

        let mut cache = self.seen_nonces.lock().unwrap();
        
        // 1. Prune expired nonces (Rule: older than 300s window)
        cache.retain(|_, ts| *ts > now - 300);

        // 2. Check for replay
        if cache.contains_key(nonce) {
            return true;
        }
        
        cache.insert(nonce.to_string(), now);
        false
    }
}

#[allow(dead_code)]
#[derive(Serialize, Deserialize, Debug, Clone)]
pub enum HandshakeMessage {
    Syn { node_id: String, timestamp: u64, nonce: String },
    SynAck { node_id: String, challenge_nonce: String, timestamp: u64, nonce: String, verifying_key: Vec<u8> },
    Ack { node_id: String, challenge_nonce: String, verifying_key: Vec<u8> },
}

#[derive(Debug, Clone, Copy, PartialEq, Eq, Serialize, Deserialize)]
pub enum TrustLevel {
    New,       // Handshake complete, but unproven
    Probation, // N packets verified
    Trusted,   // Long-term secure peer
    System,    // Local node / explicitly pinned system node
    Rejected,  // Security violation encountered (Terminal)
}

#[derive(Debug, Clone, Serialize, Deserialize)]
pub struct PeerState {
    pub public_key: Vec<u8>,
    pub trust_level: TrustLevel,
    pub last_seen: u64,
    pub packet_count: u64,
}

pub struct AdmissionManager {
    pub local_node_id: String,
    pub replay_cache: ReplayCache,
    pub peer_registry: Mutex<HashMap<String, PeerState>>, // NodeID -> State
}

impl AdmissionManager {
    pub fn new(node_id: String) -> Self {
        Self { 
            local_node_id: node_id,
            replay_cache: ReplayCache::new(),
            peer_registry: Mutex::new(HashMap::new()),
        }
    }

    /// Explicitly pin a key (System trust)
    pub fn pin_key(&self, node_id: String, public_key: Vec<u8>) {
        let mut registry = self.peer_registry.lock().unwrap();
        registry.insert(node_id, PeerState {
            public_key,
            trust_level: TrustLevel::System,
            last_seen: SystemTime::now().duration_since(UNIX_EPOCH).unwrap().as_secs(),
            packet_count: 0,
        });
    }

    /// Promote trust after successful handshake
    #[allow(dead_code)]
    pub fn register_handshake(&self, node_id: String, public_key: Vec<u8>) {
        let mut registry = self.peer_registry.lock().unwrap();
        registry.insert(node_id, PeerState {
            public_key,
            trust_level: TrustLevel::New,
            last_seen: SystemTime::now().duration_since(UNIX_EPOCH).unwrap().as_secs(),
            packet_count: 0,
        });
    }

    pub fn should_admit(&self, packet: &SignedPacket) -> bool {
        // 1. Replay Check (Rule 11/12)
        if self.replay_cache.is_replay(&packet.header.nonce) {
            warn!("Protocol: REJECT. Replay attack for nonce {}", packet.header.nonce);
            self.penalize(&packet.header.node_id);
            return false;
        }

        // 2. Identify Peer State
        let mut registry = self.peer_registry.lock().unwrap();
        let state = match registry.get_mut(&packet.header.node_id) {
            Some(s) => s,
            None => {
                if packet.header.node_id == self.local_node_id {
                    return true;
                }
                warn!("Protocol: DROP. Unknown PeerID {}", packet.header.node_id);
                return false;
            }
        };

        // 3. Rejected State Check
        if state.trust_level == TrustLevel::Rejected {
            return false;
        }

        // 4. Signature Verification
        if let Err(e) = packet.verify(&state.public_key) {
            warn!("Protocol: REJECT. Sig Violation from {}: {}", packet.header.node_id, e);
            state.trust_level = TrustLevel::Rejected; // Terminal downgrade
            return false;
        }

        // 5. Trust Promotion Logic
        state.packet_count += 1;
        state.last_seen = SystemTime::now().duration_since(UNIX_EPOCH).unwrap().as_secs();
        
        if state.trust_level == TrustLevel::New && state.packet_count >= 10 {
            info!("Protocol: PROMOTING {} to Probation", packet.header.node_id);
            state.trust_level = TrustLevel::Probation;
        }

        true
    }

    fn penalize(&self, node_id: &str) {
        let mut registry = self.peer_registry.lock().unwrap();
        if let Some(state) = registry.get_mut(node_id) {
            warn!("Protocol: Security violation. Downgrading trust for {}", node_id);
            state.trust_level = TrustLevel::Rejected;
        }
    }
}
