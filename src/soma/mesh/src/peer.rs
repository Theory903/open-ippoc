//! Peer management for the AI mesh

use serde::{Deserialize, Serialize};
use chrono::{DateTime, Utc};
use std::net::SocketAddr;
use std::collections::HashMap;
use std::path::PathBuf;
use anyhow::Result;
use crate::crypto::{NodeIdentity, SharedSecret};

/// Unique identifier for a peer (NodeID)
#[allow(dead_code)]
pub type PeerId = String;

/// Status of a peer connection
#[derive(Debug, Clone, PartialEq, Serialize, Deserialize)]
pub enum PeerStatus {
    /// Just discovered, not yet connected
    Discovered,
    /// Connecting/handshaking
    Connecting,
    /// Connected and ready
    Connected,
    /// Temporarily unavailable
    Disconnected,
    /// Blacklisted
    Blocked,
}

/// Admissions levels for trust
#[derive(Debug, Clone, Copy, PartialEq, Eq, PartialOrd, Ord, Serialize, Deserialize)]
pub enum TrustLevel {
    /// -1: Violations detected
    Blacklisted = -1,
    /// 0: Initial state
    Unknown = 0,
    /// 1: Detected via discovery
    Discovered = 1,
    /// 2: Cryptographically verified
    Authenticated = 2,
    /// 3: High reputation
    Trusted = 3,
    /// 4: User-bootstrapped
    System = 4,
}

/// A peer in the AI mesh
#[derive(Clone)]
pub struct Peer {
    /// Peer identity
    pub identity: NodeIdentity,
    /// Network address
    pub address: Option<SocketAddr>,
    /// Connection status
    pub status: PeerStatus,
    /// Trust level
    pub trust_level: TrustLevel,
    /// Shared secret (once established)
    shared_secret: Option<SharedSecret>,
    /// Last seen timestamp
    pub last_seen: DateTime<Utc>,
    /// Last message sequence
    pub last_sequence: u64,
    /// Round-trip time in ms
    pub rtt_ms: u32,
    /// Trust score (0-100)
    pub trust_score: u8,
    /// Capabilities/roles
    pub capabilities: Vec<String>,
}

impl Peer {
    /// Create a new peer from identity
    pub fn new(identity: NodeIdentity) -> Self {
        Self {
            capabilities: vec![identity.role.clone()],
            identity,
            address: None,
            status: PeerStatus::Discovered,
            trust_level: TrustLevel::Discovered,
            shared_secret: None,
            last_seen: Utc::now(),
            last_sequence: 0,
            rtt_ms: 0,
            trust_score: 50, // Neutral trust
        }
    }

    /// Set peer address
    pub fn with_address(mut self, addr: SocketAddr) -> Self {
        self.address = Some(addr);
        self
    }

    /// Set shared secret after key exchange
    pub fn set_shared_secret(&mut self, secret: SharedSecret) {
        self.shared_secret = Some(secret);
        self.status = PeerStatus::Connected;
    }

    /// Get shared secret
    pub fn shared_secret(&self) -> Option<&SharedSecret> {
        self.shared_secret.as_ref()
    }

    /// Update last seen
    pub fn touch(&mut self) {
        self.last_seen = Utc::now();
    }

    /// Set trust level
    pub fn set_trust_level(&mut self, level: TrustLevel) {
        self.trust_level = level;
    }

    /// Mark as authenticated (successfully handshaked)
    pub fn authenticate(&mut self) {
        if self.trust_level < TrustLevel::Authenticated {
            self.trust_level = TrustLevel::Authenticated;
            self.status = PeerStatus::Connected;
        }
    }

    /// Blacklist a peer for violations
    pub fn blacklist(&mut self) {
        self.trust_level = TrustLevel::Blacklisted;
        self.status = PeerStatus::Blocked;
    }

    /// Update trust score and handle promotions
    pub fn update_trust(&mut self, delta: i8) {
        let new_score = self.trust_score as i16 + delta as i16;
        self.trust_score = new_score.clamp(0, 100) as u8;

        // Auto-promotion logic (DISCOVERED -> TRUSTED)
        if self.trust_level == TrustLevel::Authenticated && self.trust_score >= 80 {
            self.trust_level = TrustLevel::Trusted;
        }
    }

    /// Check if peer is available for communication
    pub fn is_available(&self) -> bool {
        matches!(self.status, PeerStatus::Connected)
    }

    /// Check if peer has a specific capability
    pub fn has_capability(&self, cap: &str) -> bool {
        self.capabilities.iter().any(|c| c == cap)
    }

    /// Serialize peer info for discovery broadcast
    pub fn to_discovery_info(&self) -> serde_json::Value {
        serde_json::json!({
            "id": self.identity.id,
            "name": self.identity.name,
            "role": self.identity.role,
            "exchange_public": hex::encode(&self.identity.exchange_public),
            "signing_public": hex::encode(&self.identity.signing_public),
            "capabilities": self.capabilities,
            "address": self.address.map(|a| a.to_string()),
        })
    }
}

/// Peer table for managing multiple peers
#[allow(dead_code)]
pub struct PeerTable {
    pub peers: std::collections::HashMap<String, Peer>,
}

impl PeerTable {
    #![allow(dead_code)]
    pub fn new() -> Self {
        Self {
            peers: std::collections::HashMap::new(),
        }
    }

    /// Add or update a peer
    pub fn upsert(&mut self, peer: Peer) {
        self.peers.insert(peer.identity.id.clone(), peer);
    }

    /// Get a peer by ID
    pub fn get(&self, id: &str) -> Option<&Peer> {
        self.peers.get(id)
    }

    /// Get a mutable peer by ID
    pub fn get_mut(&mut self, id: &str) -> Option<&mut Peer> {
        self.peers.get_mut(id)
    }

    /// Remove a peer
    pub fn remove(&mut self, id: &str) -> Option<Peer> {
        self.peers.remove(id)
    }

    /// Get all connected peers
    pub fn connected(&self) -> impl Iterator<Item = &Peer> {
        self.peers.values().filter(|p| p.is_available())
    }

    /// Get peers with specific capability
    pub fn with_capability(&self, cap: &str) -> Vec<&Peer> {
        self.peers.values()
            .filter(|p| p.is_available() && p.has_capability(cap))
            .collect()
    }

    /// Get all peer IDs
    pub fn ids(&self) -> Vec<String> {
        self.peers.keys().cloned().collect()
    }

    /// Count connected peers
    pub fn connected_count(&self) -> usize {
        self.connected().count()
    }
}

impl Default for PeerTable {
    fn default() -> Self {
        Self::new()
    }
}

/// Metadata for reputation persistence
#[derive(Debug, Serialize, Deserialize, Clone)]
pub struct ReputationEntry {
    pub id: String,
    pub trust_level: TrustLevel,
    pub trust_score: u8,
    pub last_seen: chrono::DateTime<chrono::Utc>,
}

/// Manages persistence of peer reputation
pub struct ReputationManager {
    path: PathBuf,
}

impl ReputationManager {
    pub fn new(path: PathBuf) -> Self {
        Self { path }
    }

    /// Save peer table to disk
    pub fn save(&self, peers: &HashMap<String, Peer>) -> Result<()> {
        let entries: Vec<ReputationEntry> = peers.values()
            .map(|p| ReputationEntry {
                id: p.identity.id.clone(),
                trust_level: p.trust_level,
                trust_score: p.trust_score,
                last_seen: chrono::Utc::now(),
            })
            .collect();

        let json = serde_json::to_string_pretty(&entries)?;
        if let Some(parent) = self.path.parent() {
            std::fs::create_dir_all(parent)?;
        }
        std::fs::write(&self.path, json)?;
        Ok(())
    }

    /// Load peer data from disk
    pub fn load(&self) -> Result<Vec<ReputationEntry>> {
        if !self.path.exists() {
            return Ok(vec![]);
        }
        let json = std::fs::read_to_string(&self.path)?;
        let entries: Vec<ReputationEntry> = serde_json::from_str(&json)?;
        Ok(entries)
    }
}
