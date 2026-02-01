//! AI Mesh Network - Main orchestrator for P2P AI communication

use anyhow::Result;
use std::net::SocketAddr;
use std::sync::Arc;
use tokio::sync::{mpsc, RwLock, broadcast};
use tracing::{info, warn, debug};
use uuid::Uuid;

use sha2::Digest;
use std::collections::{HashSet, VecDeque};
use crate::crypto::{NodeSecrets, NodeIdentity, encrypt_message, decrypt_message, verify_signature};
use crate::messages::{AiMessage, MessageType, Thought, Broadcast};
use crate::peer::{Peer, PeerTable, ReputationManager};
use crate::identity::PersistentIdentity;
use std::path::PathBuf;

/// Configuration for the AI mesh
#[derive(Debug, Clone)]
pub struct MeshConfig {
    /// Node name
    pub name: String,
    /// Node role (reasoning, retrieval, tool, relay)
    pub role: String,
    /// Listen port
    pub port: u16,
    /// Base Data Directory (e.g., /var/lib/ippoc/nodes) or (.)
    pub data_dir: PathBuf,
    /// Maximum peers
    pub max_peers: usize,
    /// Heartbeat interval (seconds)
    pub heartbeat_secs: u64,
    /// Enable encryption
    pub encrypted: bool,
}

impl Default for MeshConfig {
    fn default() -> Self {
        Self {
            name: format!("node-{}", Uuid::new_v4().to_string().split('-').next().unwrap()),
            role: "tool".to_string(),
            port: 8080,
            data_dir: PathBuf::from("."),
            max_peers: 100,
            heartbeat_secs: 30,
            encrypted: true,
        }
    }
}

/// The AI Mesh - manages P2P communication between AI nodes
pub struct AiMesh {
    /// Our secrets
    secrets: NodeSecrets,
    /// Our public identity
    identity: NodeIdentity,
    /// Configuration
    config: MeshConfig,
    /// Connected peers
    peers: Arc<RwLock<PeerTable>>,
    /// Reputation manager for persistence
    reputation_manager: Arc<ReputationManager>,
    /// Replay cache to prevent replay attacks
    replay_cache: Arc<RwLock<ReplayCache>>,
    /// Outgoing message channel
    outbox: mpsc::Sender<AiMessage>,
    /// Incoming message broadcast
    inbox: broadcast::Sender<AiMessage>,
    /// Message sequence counter
    sequence: Arc<RwLock<u64>>,

    /// Stop networking
    running: Arc<RwLock<bool>>,
   
    /// Networking transport (QUIC)
    transport: Arc<RwLock<Option<Arc<crate::transport::QuicTransport>>>>,
    
    /// Root directory for this specific node (e.g. data/nodes/<ID>/)
    pub node_root: PathBuf,

    /// Metabolic Controller (Economy)
    pub economy: Arc<RwLock<crate::economy::EconomyController>>,
}

impl AiMesh {
    /// Create a new AI mesh
    pub fn new(config: MeshConfig) -> (Self, mpsc::Receiver<AiMessage>, broadcast::Receiver<AiMessage>) {
        let (outbox_tx, outbox_rx) = mpsc::channel(100);
        let (inbox_tx, inbox_rx) = broadcast::channel(100); 

        // --- SOVEREIGN BOOT SEQUENCE (Phase 1.1) ---
        // 1. Load or Generate Identity (Hardware Bound)
        let (persisted_identity, node_root) = crate::identity::load_or_create_identity(&config.data_dir, &config.role, &config.name)
            .expect("CRITICAL: Sovereign Boot Failed! Hardware Mismatch or FS Error. HALTING.");
            
        let secrets = persisted_identity.secrets().expect("Failed to derive secrets");
        let identity = persisted_identity.identity;

        info!("Identity Authenticated: {} ({})", identity.name, identity.id);
        info!("Sovereign Node Root: {:?}", node_root);
        
        // 2. Initialize Subsystems inside Node Root
        
        // Reputation
        let reputation_path = node_root.join("data").join("reputation.json");
        let reputation_manager = Arc::new(ReputationManager::new(reputation_path));

        // Economy (Phase 2)
        info!("Initializing Metabolism...");
        let economy_controller = crate::economy::EconomyController::new(&identity.id, &node_root)
            .expect("Failed to initialize Economy Controller");
        let economy = Arc::new(RwLock::new(economy_controller));

        let mut peer_table = PeerTable::new();
        // Load persisted reputation
        if let Ok(entries) = reputation_manager.load() {
            info!("Loaded {} peers from reputation DB", entries.len());
            for entry in entries {
                let mut peer = Peer::new(NodeIdentity {
                    id: entry.id.clone(),
                    exchange_public: [0u8; 32], 
                    signing_public: [0u8; 32],
                    role: "unknown".into(),
                    name: "unknown".into(),
                });
                peer.set_trust_level(entry.trust_level);
                peer.update_trust(entry.trust_score as i8 - peer.trust_score as i8);
                peer_table.upsert(peer);
            }
        }

        let mesh = Self {
            secrets,
            identity,
            config,
            peers: Arc::new(RwLock::new(peer_table)),
            reputation_manager,
            replay_cache: Arc::new(RwLock::new(ReplayCache::new(1000))),
            outbox: outbox_tx,
            inbox: inbox_tx,
            sequence: Arc::new(RwLock::new(0)),
            running: Arc::new(RwLock::new(false)),
            transport: Arc::new(RwLock::new(None)),
            node_root,
            economy,
        };
        
        (mesh, outbox_rx, inbox_rx)
    }

    /// Start the networking layer (bind port)
    pub async fn start_networking(&self) -> Result<()> {
        let mut running = self.running.write().await;
        if *running {
            return Ok(());
        }
        
        info!("Starting AI Mesh networking on port {}", self.config.port);
        
        let inbox_tx = self.inbox.clone();
        let (tx, mut rx) = mpsc::channel(100);
        
        // Bind QUIC transport
        let transport = Arc::new(crate::transport::QuicTransport::bind(self.config.port, tx).await?);
        
        // Attempt WAN mapping (Fire and forget? No, let's log it)
        let _ = crate::transport::QuicTransport::map_port_upnp(self.config.port).await;

        {
            let mut t = self.transport.write().await;
            *t = Some(transport.clone());
        }
        
        // Spawn incoming message handler
        tokio::spawn(async move {
            while let Some(msg) = rx.recv().await {
                 let _ = inbox_tx.send(msg);
            }
        });
        
        *running = true;
        Ok(())
    }

    /// Get our identity
    pub fn identity(&self) -> &NodeIdentity {
        &self.identity
    }

    /// Get next sequence number
    async fn next_sequence(&self) -> u64 {
        let mut seq = self.sequence.write().await;
        *seq += 1;
        *seq
    }

    /// Add a peer
    pub async fn add_peer(&self, peer: Peer) {
        let mut peers = self.peers.write().await;
        info!("Adding peer: {} ({})", peer.identity.name, peer.identity.role);
        peers.upsert(peer);
    }

    /// Connect to a peer by address
    pub async fn connect_to(&self, addr: SocketAddr) -> Result<()> {
        info!("Connecting to peer at {}", addr);
        // In production, this would:
        // 1. Open QUIC connection
        // 2. Exchange identities
        // 3. Perform key exchange
        // 4. Add to peer table
        Ok(())
    }

    /// Send a thought to the mesh
    pub async fn send_thought(&self, thought: Thought) -> Result<()> {
        let seq = self.next_sequence().await;
        let mut msg = AiMessage::thought(&self.identity.id, &thought, seq);
        
        // Sign the message
        msg.signature = hex::encode(self.secrets.sign(&msg.payload));
        
        self.outbox.send(msg).await?;
        Ok(())
    }

    /// Broadcast a message to all peers
    pub async fn broadcast(&self, broadcast: Broadcast) -> Result<()> {
        let seq = self.next_sequence().await;
        let mut msg = AiMessage::broadcast(&self.identity.id, &broadcast, seq);
        
        msg.signature = hex::encode(self.secrets.sign(&msg.payload));
        
        self.outbox.send(msg).await?;
        Ok(())
    }

    /// Send a direct message to a specific peer
    pub async fn send_direct(&self, recipient: &str, content: serde_json::Value) -> Result<()> {
        let peers = self.peers.read().await;
        let peer = peers.get(recipient)
            .ok_or_else(|| anyhow::anyhow!("Peer not found: {}", recipient))?;
        
        // Encrypt if we have a shared secret
        let payload = if let Some(secret) = peer.shared_secret() {
            let plaintext = serde_json::to_vec(&content)?;
            encrypt_message(secret, &plaintext)?
        } else {
            serde_json::to_vec(&content)?
        };
        
        drop(peers);
        
        let seq = self.next_sequence().await;
        let mut msg = AiMessage::direct(&self.identity.id, recipient, content, seq);
        msg.payload = payload;
        msg.signature = hex::encode(self.secrets.sign(&msg.payload));
        
        self.outbox.send(msg).await?;
        Ok(())
    }

    /// Handle an incoming message
    pub async fn handle_message(&self, msg: AiMessage) -> Result<()> {
        debug!("Received message from {} (type: {:?})", msg.sender, msg.msg_type);
        
        // 1. Reputation Filter (PRD 09)
        {
            let peers = self.peers.read().await;
            if let Some(peer) = peers.get(&msg.sender) {
                if peer.trust_level == crate::peer::TrustLevel::Blacklisted || peer.trust_score < 10 {
                    warn!("Rejecting message from low-reputation peer: {}", msg.sender);
                    return Ok(());
                }
            }
        }

        // Verify signature
        {
            let peers = self.peers.read().await;
            if let Some(peer) = peers.get(&msg.sender) {
                if let Ok(sig_bytes) = hex::decode(&msg.signature) {
                    if sig_bytes.len() == 64 {
                        let mut sig_arr = [0u8; 64];
                        sig_arr.copy_from_slice(&sig_bytes);
                        if !verify_signature(&peer.identity.signing_public, &msg.payload, &sig_arr)? {
                            warn!("Invalid signature from peer {}", msg.sender);
                            return Ok(());
                        }
                    }
                }
            }
        }

        // Verify nonce (Replay Protection)
        {
            let mut cache = self.replay_cache.write().await;
            if !cache.check_and_add(msg.nonce) {
                warn!("Replay attack detected or duplicate nonce: {} from {}", msg.nonce, msg.sender);
                return Ok(());
            }
        }
        
        // Match message type
        let result = match msg.msg_type {
            MessageType::Discovery => {
                self.handle_discovery(&msg).await
            }
            MessageType::Thought | MessageType::Broadcast => {
                // Forward to inbox
                let _ = self.inbox.send(msg);
                Ok(())
            }
            MessageType::Direct => {
                // Decrypt and forward
                if msg.recipient.as_ref() == Some(&self.identity.id) {
                    self.handle_direct(&msg).await
                } else {
                    // If not for us, maybe forward or drop
                    Ok(())
                }
            }
            MessageType::Handshake => {
                // Secure handshake bridge
                self.handle_handshake(&msg).await
            }
            _ => {
                // Forward to inbox for application handling
                let _ = self.inbox.send(msg);
                Ok(())
            }
        };

        // Persist reputation if it changed (optimization: only save some times)
        // For now, let's save on every message to ensure persistence
        let peers = self.peers.read().await;
        let _ = self.reputation_manager.save(&peers.peers);

        result
    }

    async fn handle_discovery(&self, msg: &AiMessage) -> Result<()> {
        let info: serde_json::Value = serde_json::from_slice(&msg.payload)?;
        info!("Discovery from peer: {:?}", info.get("name"));
        
        // Parse and add peer
        if let (Some(id), Some(name), Some(role)) = (
            info.get("id").and_then(|v| v.as_str()),
            info.get("name").and_then(|v| v.as_str()),
            info.get("role").and_then(|v| v.as_str()),
        ) {
            let exchange_public = info.get("exchange_public")
                .and_then(|v| v.as_str())
                .and_then(|s| hex::decode(s).ok())
                .map(|b| {
                    let mut arr = [0u8; 32];
                    arr.copy_from_slice(&b);
                    arr
                })
                .unwrap_or([0u8; 32]);
            
            let signing_public = info.get("signing_public")
                .and_then(|v| v.as_str())
                .and_then(|s| hex::decode(s).ok())
                .map(|b| {
                    let mut arr = [0u8; 32];
                    arr.copy_from_slice(&b);
                    arr
                })
                .unwrap_or([0u8; 32]);
            
            let identity = NodeIdentity {
                id: id.to_string(),
                exchange_public,
                signing_public,
                role: role.to_string(),
                name: name.to_string(),
            };
            
            let mut peer = Peer::new(identity);
            
            // Derive shared secret
            let shared = self.secrets.derive_shared(&peer.identity.exchange_public);
            peer.set_shared_secret(shared);
            
            self.add_peer(peer).await;
        }
        
        Ok(())
    }

    async fn handle_direct(&self, msg: &AiMessage) -> Result<()> {
        let peers = self.peers.read().await;
        
        if let Some(peer) = peers.get(&msg.sender) {
            if let Some(secret) = peer.shared_secret() {
                let plaintext = decrypt_message(secret, &msg.payload)?;
                let content: serde_json::Value = serde_json::from_slice(&plaintext)?;
                info!("Direct message from {}: {:?}", peer.identity.name, content);
            }
        }
        
        let _ = self.inbox.send(msg.clone());
        Ok(())
    }

    /// Get connected peer count
    pub async fn peer_count(&self) -> usize {
        self.peers.read().await.connected_count()
    }

    /// Get peers with specific capability
    pub async fn peers_with_capability(&self, cap: &str) -> Vec<String> {
        self.peers.read().await
            .with_capability(cap)
            .iter()
            .map(|p| p.identity.id.clone())
            .collect()
    }

    /// Initiate a handshake with a peer
    pub async fn initiate_handshake(&self, peer_id: &str) -> Result<()> {
        let peers = self.peers.read().await;
        let _peer = peers.get(peer_id)
            .ok_or_else(|| anyhow::anyhow!("Peer not found: {}", peer_id))?;
        
        let mut nonce = [0u8; 16];
        getrandom::getrandom(&mut nonce)?;

        let hs = crate::messages::HandshakeMessage {
            kind: crate::messages::HandshakeKind::Syn,
            exchange_public: self.identity.exchange_public,
            signing_public: self.identity.signing_public,
            nonce,
            challenge: None,
        };

        let mut msg = AiMessage::handshake(&self.identity.id, Some(peer_id), &hs);
        msg.signature = hex::encode(self.secrets.sign(&msg.payload));
        
        drop(peers);
        self.outbox.send(msg).await?;
        
        info!("Initiated handshake with {}", peer_id);
        Ok(())
    }

    /// Handle handshake sequence
    async fn handle_handshake(&self, msg: &AiMessage) -> Result<()> {
        let hs: crate::messages::HandshakeMessage = serde_json::from_slice(&msg.payload)?;
        info!("Handshake {:?} from {}", hs.kind, msg.sender);

        let mut peers = self.peers.write().await;
        
        match hs.kind {
            crate::messages::HandshakeKind::Syn => {
                // Node A -> Node B (SYN)
                // 1. Verify NodeID matches signing public key
                let derived_id = hex::encode(sha2::Sha256::digest(&hs.signing_public));
                if derived_id != msg.sender {
                    warn!("Handshake NodeID mismatch for {}", msg.sender);
                    return Ok(());
                }

                // 2. Pin public key / Create peer
                let mut peer = Peer::new(NodeIdentity {
                    id: msg.sender.clone(),
                    exchange_public: hs.exchange_public,
                    signing_public: hs.signing_public,
                    role: "unknown".to_string(), // To be updated via discovery
                    name: "unknown".to_string(),
                });
                
                // 3. Derive shared secret
                let shared = self.secrets.derive_shared(&hs.exchange_public);
                peer.set_shared_secret(shared.clone());
                peer.set_trust_level(crate::peer::TrustLevel::Discovered);
                
                // 4. Respond with SYN-ACK
                let mut resp_nonce = [0u8; 16];
                getrandom::getrandom(&mut resp_nonce)?;
                
                // Challenge: Encrypt A's nonce with our shared secret
                let challenge = crate::crypto::encrypt_message(&shared, &hs.nonce)?;

                let resp_hs = crate::messages::HandshakeMessage {
                    kind: crate::messages::HandshakeKind::SynAck,
                    exchange_public: self.identity.exchange_public,
                    signing_public: self.identity.signing_public,
                    nonce: resp_nonce,
                    challenge: Some(challenge),
                };

                peers.upsert(peer);
                
                let mut resp_msg = AiMessage::handshake(&self.identity.id, Some(&msg.sender), &resp_hs);
                resp_msg.signature = hex::encode(self.secrets.sign(&resp_msg.payload));
                
                self.outbox.send(resp_msg).await?;
            }
            crate::messages::HandshakeKind::SynAck => {
                // Node B -> Node A (SYN-ACK)
                if let Some(peer) = peers.get_mut(&msg.sender) {
                    if let (Some(shared), Some(challenge)) = (peer.shared_secret(), hs.challenge) {
                        // 1. Verify challenge (B decrypted our nonce)
                        let decrypted_nonce = crate::crypto::decrypt_message(shared, &challenge)?;
                        if decrypted_nonce.len() != 16 {
                            warn!("Invalid handshake challenge from {}", msg.sender);
                            return Ok(());
                        }

                        // 2. Respond with ACK
                        let resp_hs = crate::messages::HandshakeMessage {
                            kind: crate::messages::HandshakeKind::Ack,
                            exchange_public: self.identity.exchange_public,
                            signing_public: self.identity.signing_public,
                            nonce: hs.nonce, // Echo B's nonce
                            challenge: None,
                        };

                        peer.authenticate();
                        info!("Handshake completed with {}", msg.sender);

                        let mut resp_msg = AiMessage::handshake(&self.identity.id, Some(&msg.sender), &resp_hs);
                        resp_msg.signature = hex::encode(self.secrets.sign(&resp_msg.payload));
                        
                        self.outbox.send(resp_msg).await?;
                    }
                }
            }
            crate::messages::HandshakeKind::Ack => {
                // Node A -> Node B (ACK)
                if let Some(peer) = peers.get_mut(&msg.sender) {
                    peer.authenticate();
                    info!("Handshake finalized with {}", msg.sender);
                }
            }
        }

        Ok(())
    }

    /// Broadcast discovery message
    pub async fn announce(&self) -> Result<()> {
        let discovery_info = serde_json::json!({
            "id": self.identity.id,
            "name": self.identity.name,
            "role": self.identity.role,
            "exchange_public": hex::encode(&self.identity.exchange_public),
            "signing_public": hex::encode(&self.identity.signing_public),
            "capabilities": vec![&self.identity.role],
            "port": self.config.port,
        });
        
        let msg = AiMessage::discovery(&self.identity.id, discovery_info);
        self.outbox.send(msg).await?;
        
        info!("Announced to mesh");
        Ok(())
    }
}

#[cfg(test)]
mod tests {
    use super::*;
    
    #[tokio::test]
    async fn test_handshake_sequence() -> Result<()> {
        let config_a = MeshConfig { name: "node-a".into(), ..Default::default() };
        let config_b = MeshConfig { name: "node-b".into(), ..Default::default() };
        
        let (mesh_a, mut out_a, _in_a) = AiMesh::new(config_a);
        let (mesh_b, mut out_b, _in_b) = AiMesh::new(config_b);

        let id_a = mesh_a.identity().id.clone();
        let id_b = mesh_b.identity().id.clone();

        // 1. Discovery (Simulated)
        let peer_b = Peer::new(mesh_b.identity().clone());
        let discovery_info = peer_b.to_discovery_info();
        let disc_msg = AiMessage::discovery(&id_b, discovery_info);
        mesh_a.handle_message(disc_msg).await?;

        // 2. Node A initiates SYN
        mesh_a.initiate_handshake(&id_b).await?;
        let msg_syn = out_a.recv().await.expect("A outbox should have SYN");
        
        // 3. Node B handles SYN and sends SYN-ACK
        mesh_b.handle_message(msg_syn).await?;
        let msg_syn_ack = out_b.recv().await.expect("B outbox should have SYN-ACK");
        
        // 4. Node A handles SYN-ACK and sends ACK
        mesh_a.handle_message(msg_syn_ack).await?;
        let msg_ack = out_a.recv().await.expect("A outbox should have ACK");
        
        // 5. Node B handles ACK
        mesh_b.handle_message(msg_ack).await?;

        // 6. Verify authentication
        let peers_a = mesh_a.peers.read().await;
        let peers_b = mesh_b.peers.read().await;
        
        assert_eq!(peers_a.get(&id_b).unwrap().trust_level, crate::peer::TrustLevel::Authenticated);
        assert_eq!(peers_b.get(&id_a).unwrap().trust_level, crate::peer::TrustLevel::Authenticated);

        Ok(())
    }

    #[tokio::test]
    async fn test_replay_protection() -> Result<()> {
        let config = MeshConfig { name: "test-node".into(), ..Default::default() };
        let (mesh, _out, _in) = AiMesh::new(config);

        let mut msg = AiMessage::thought("sender", &Thought {
            content: serde_json::json!({"test": "data"}),
            embedding: None,
            confidence: 1.0,
            context: None,
            tags: vec![],
        }, 0);
        
        // First time is okay
        let mut cache = mesh.replay_cache.write().await;
        assert!(cache.check_and_add(msg.nonce));
        
        // Second time with same nonce is REJECTED
        assert!(!cache.check_and_add(msg.nonce));
        
        // Different nonce is okay
        msg.nonce += 1;
        assert!(cache.check_and_add(msg.nonce));

        Ok(())
    }

    #[tokio::test]
    async fn test_reputation_persistence() -> Result<()> {
        let temp_path = std::env::temp_dir().join(format!("reputation_{}.json", Uuid::new_v4()));
        let config = MeshConfig { 
            name: "test-node".into(), 
            reputation_path: Some(temp_path.clone()),
            ..Default::default() 
        };
        
        {
            let (mesh, _out, _in) = AiMesh::new(config.clone());
            let mut peer = Peer::new(NodeIdentity {
                id: "peer-1".into(),
                exchange_public: [0u8; 32],
                signing_public: [0u8; 32],
                role: "test".into(),
                name: "test".into(),
            });
            peer.set_trust_level(crate::peer::TrustLevel::Trusted);
            peer.update_trust(30); // 50 + 30 = 80
            
            mesh.add_peer(peer).await;
            
            // Trigger save
            let peers = mesh.peers.read().await;
            mesh.reputation_manager.save(&peers.peers)?;
        }

        // Reload in new mesh instance
        let (mesh2, _out2, _in2) = AiMesh::new(config);
        let peers2 = mesh2.peers.read().await;
        let peer2 = peers2.get("peer-1").expect("Peer should be reloaded");
        
        assert_eq!(peer2.trust_level, crate::peer::TrustLevel::Trusted);
        assert_eq!(peer2.trust_score, 80);

        std::fs::remove_file(temp_path)?;
        Ok(())
    }

    #[tokio::test]
    async fn test_identity_persistence() -> Result<()> {
        let temp_dir = std::env::temp_dir().join(Uuid::new_v4().to_string());
        std::fs::create_dir_all(&temp_dir)?;
        let identity_path = temp_dir.join("identity.key");
        
        // 1. First Boot: Generate
        let config = MeshConfig { 
            name: "test-node".into(), 
            identity_path: Some(identity_path.clone()),
            ..Default::default() 
        };
        
        let (mesh1, _, _) = AiMesh::new(config.clone());
        let id1 = mesh1.identity().id.clone();
        
        assert!(identity_path.exists());
        
        // 2. Second Boot: Load
        let (mesh2, _, _) = AiMesh::new(config);
        let id2 = mesh2.identity().id.clone();
        
        // IDs must match
        assert_eq!(id1, id2);
        
        // 3. Verify Perms (Unix only)
        #[cfg(target_family = "unix")]
        {
            use std::os::unix::fs::PermissionsExt;
            let meta = std::fs::metadata(&identity_path)?;
            let mode = meta.permissions().mode();
            assert_eq!(mode & 0o777, 0o600, "Key file must be 0600");
        }

        std::fs::remove_dir_all(temp_dir)?;
        Ok(())
    }
}

/// Cache to prevent message replay attacks
struct ReplayCache {
    /// Seen nonces
    seen: HashSet<u64>,
    /// Order of arrival for eviction
    order: VecDeque<u64>,
    /// Maximum capacity
    capacity: usize,
}

impl ReplayCache {
    fn new(capacity: usize) -> Self {
        Self {
            seen: HashSet::with_capacity(capacity),
            order: VecDeque::with_capacity(capacity),
            capacity,
        }
    }

    /// Check if nonce is new and add it if so. Returns true if unique.
    fn check_and_add(&mut self, nonce: u64) -> bool {
        if self.seen.contains(&nonce) {
            return false;
        }

        if self.order.len() >= self.capacity {
            if let Some(old) = self.order.pop_front() {
                self.seen.remove(&old);
            }
        }

        self.seen.insert(nonce);
        self.order.push_back(nonce);
        true
    }
}
