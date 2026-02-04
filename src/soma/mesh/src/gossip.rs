//! Encrypted Gossip Protocol (EGP)
//! Probabilistic message forwarding with encryption and deniability

use serde::{Deserialize, Serialize};
use std::collections::{HashMap, HashSet};
use std::sync::Arc;
use tokio::sync::RwLock;
use rand::Rng;
use sha2::{Sha256, Digest};
use aes_gcm::{
    aead::{Aead, KeyInit},
    Aes256Gcm, Nonce,
};
use x25519_dalek::{PublicKey, StaticSecret};
use ed25519_dalek::{Keypair, Signature, Signer, Verifier};

#[derive(Debug, Clone, Serialize, Deserialize)]
pub struct GossipMessage {
    pub id: String,
    pub payload: Vec<u8>,
    pub timestamp: u64,
    pub ttl: u64,
    pub origin: String,
    pub hops: usize,
    pub signature: Vec<u8>,
}

#[derive(Debug, Clone, Serialize, Deserialize)]
pub struct EncryptedGossipPacket {
    pub ephemeral_pubkey: Vec<u8>,
    pub nonce: Vec<u8>,
    pub ciphertext: Vec<u8>,
    pub mac: Vec<u8>,
}

pub struct GossipNode {
    node_id: String,
    identity_keypair: Keypair,
    known_peers: Arc<RwLock<HashMap<String, PublicKey>>>,
    seen_messages: Arc<RwLock<HashSet<String>>>,
    message_buffer: Arc<RwLock<Vec<GossipMessage>>>,
    forward_probability: f64,
}

impl GossipNode {
    pub fn new(node_id: String) -> Self {
        let mut rng = rand::thread_rng();
        let identity_keypair = Keypair::generate(&mut rng);
        
        Self {
            node_id,
            identity_keypair,
            known_peers: Arc::new(RwLock::new(HashMap::new())),
            seen_messages: Arc::new(RwLock::new(HashSet::new())),
            message_buffer: Arc::new(RwLock::new(Vec::new())),
            forward_probability: 0.6,
        }
    }

    pub async fn add_peer(&self, peer_id: String, pubkey: PublicKey) {
        self.known_peers.write().await.insert(peer_id, pubkey);
    }

    pub fn sign_message(&self, message: &mut GossipMessage) -> Result<(), Box<dyn std::error::Error>> {
        let mut hasher = Sha256::new();
        hasher.update(&message.payload);
        hasher.update(message.timestamp.to_le_bytes());
        hasher.update(message.ttl.to_le_bytes());
        let digest = hasher.finalize();
        
        let signature = self.identity_keypair.sign(&digest);
        message.signature = signature.to_bytes().to_vec();
        Ok(())
    }

    pub fn verify_signature(&self, message: &GossipMessage, pubkey: &PublicKey) -> bool {
        let mut hasher = Sha256::new();
        hasher.update(&message.payload);
        hasher.update(message.timestamp.to_le_bytes());
        hasher.update(message.ttl.to_le_bytes());
        let digest = hasher.finalize();
        
        if let Ok(signature) = ed25519_dalek::Signature::try_from(message.signature.as_slice()) {
            pubkey.verify(&digest, &signature).is_ok()
        } else {
            false
        }
    }

    pub fn encrypt_for_peer(&self, payload: &[u8], peer_pubkey: &PublicKey) -> Result<EncryptedGossipPacket, Box<dyn std::error::Error>> {
        let mut rng = rand::thread_rng();
        
        // Generate ephemeral keypair
        let ephemeral_secret = StaticSecret::random_from_rng(&mut rng);
        let ephemeral_public = PublicKey::from(&ephemeral_secret);
        
        // Derive shared secret
        let shared_secret = ephemeral_secret.diffie_hellman(peer_pubkey);
        let key = derive_aes_key(&shared_secret.to_bytes());
        
        // Encrypt payload
        let cipher = Aes256Gcm::new(&key.into());
        let nonce = Nonce::from_slice(&rng.gen::<[u8; 12]>());
        
        let ciphertext = cipher.encrypt(nonce, payload)?;
        
        Ok(EncryptedGossipPacket {
            ephemeral_pubkey: ephemeral_public.as_bytes().to_vec(),
            nonce: nonce.as_slice().to_vec(),
            ciphertext,
            mac: vec![], // MAC is included in ciphertext in AES-GCM
        })
    }

    pub async fn receive_message(&self, packet: EncryptedGossipPacket) -> Result<Option<GossipMessage>, Box<dyn std::error::Error>> {
        // Decrypt using our identity key
        let shared_secret = self.identity_keypair.secret.expand_edwards()?.to_montgomery()?.to_bytes();
        let key = derive_aes_key(&shared_secret);
        let cipher = Aes256Gcm::new(&key.into());
        let nonce = Nonce::from_slice(&packet.nonce);
        
        let plaintext = cipher.decrypt(nonce, packet.ciphertext.as_ref())?;
        let message: GossipMessage = bincode::deserialize(&plaintext)?;
        
        // Check if we've seen this message
        let message_id = message.id.clone();
        if self.seen_messages.read().await.contains(&message_id) {
            return Ok(None);
        }
        
        // Verify signature
        if let Some(origin_pubkey) = self.known_peers.read().await.get(&message.origin) {
            if !self.verify_signature(&message, origin_pubkey) {
                return Err("Invalid signature".into());
            }
        }
        
        // Mark as seen
        self.seen_messages.write().await.insert(message_id);
        
        // Buffer for potential forwarding
        if message.hops < 5 && message.ttl > std::time::SystemTime::now().duration_since(std::time::UNIX_EPOCH)?.as_secs() {
            self.message_buffer.write().await.push(message.clone());
        }
        
        Ok(Some(message))
    }

    pub async fn forward_messages(&self) -> Vec<(String, EncryptedGossipPacket)> {
        let mut forwards = Vec::new();
        let mut buffer = self.message_buffer.write().await;
        let peers = self.known_peers.read().await;
        
        let mut rng = rand::thread_rng();
        
        buffer.retain(|msg| {
            if msg.hops >= 5 || msg.ttl <= std::time::SystemTime::now().duration_since(std::time::UNIX_EPOCH).unwrap().as_secs() {
                return false;
            }
            
            // Probabilistic forwarding
            if rng.gen::<f64>() < self.forward_probability {
                msg.hops += 1;
                
                // Send to random subset of peers
                let peer_subset: Vec<_> = peers.iter().take(3).collect();
                for (peer_id, pubkey) in peer_subset {
                    if let Ok(packet) = self.encrypt_for_peer(&bincode::serialize(msg).unwrap(), pubkey) {
                        forwards.push((peer_id.clone(), packet));
                    }
                }
            }
            true
        });
        
        forwards
    }

    pub async fn broadcast(&self, payload: Vec<u8>, ttl_seconds: u64) -> Result<GossipMessage, Box<dyn std::error::Error>> {
        let message_id = format!("{}-{}", self.node_id, std::time::SystemTime::now().duration_since(std::time::UNIX_EPOCH)?.as_nanos());
        
        let mut message = GossipMessage {
            id: message_id,
            payload,
            timestamp: std::time::SystemTime::now().duration_since(std::time::UNIX_EPOCH)?.as_secs(),
            ttl: std::time::SystemTime::now().duration_since(std::time::UNIX_EPOCH)?.as_secs() + ttl_seconds,
            origin: self.node_id.clone(),
            hops: 0,
            signature: vec![],
        };
        
        self.sign_message(&mut message)?;
        self.seen_messages.write().await.insert(message.id.clone());
        self.message_buffer.write().await.push(message.clone());
        
        Ok(message)
    }
}

fn derive_aes_key(shared_secret: &[u8; 32]) -> [u8; 32] {
    let mut hasher = Sha256::new();
    hasher.update(shared_secret);
    hasher.update(b"EGP_KEY_DERIVATION");
    let result = hasher.finalize();
    let mut key = [0u8; 32];
    key.copy_from_slice(&result[..32]);
    key
}

#[cfg(test)]
mod tests {
    use super::*;
    
    #[tokio::test]
    async fn test_gossip_protocol() {
        let node1 = GossipNode::new("node1".to_string());
        let node2 = GossipNode::new("node2".to_string());
        
        // Exchange public keys
        node1.add_peer("node2".to_string(), node2.identity_keypair.public).await;
        node2.add_peer("node1".to_string(), node1.identity_keypair.public).await;
        
        // Broadcast message
        let message = node1.broadcast(b"test message".to_vec(), 300).await.unwrap();
        
        // Create packet for node2
        let packet = node1.encrypt_for_peer(&bincode::serialize(&message).unwrap(), &node2.identity_keypair.public).unwrap();
        
        // Receive and verify
        let received = node2.receive_message(packet).await.unwrap().unwrap();
        assert_eq!(received.payload, b"test message");
        assert_eq!(received.origin, "node1");
    }
}