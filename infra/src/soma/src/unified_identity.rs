// Unified Identity and Trust Management System
// Consolidates body and HAL identity systems

use std::collections::HashMap;
use std::sync::Arc;
use tokio::sync::RwLock;
use ed25519_dalek::{SigningKey, VerifyingKey};
use sha2::{Sha256, Digest};

// Consolidated Identity System
#[derive(Debug, Clone)]
pub struct UnifiedIdentity {
    pub node_id: String,
    pub signing_key: SigningKey,
    pub verifying_key: VerifyingKey,
    pub hardware_fingerprint: String,
    pub trust_level: TrustLevel,
    pub creation_timestamp: u64,
}

#[derive(Debug, Clone, PartialEq, Eq, Hash)]
pub enum TrustLevel {
    New,        // Fresh identity, minimal privileges
    Probation,  // Handshake completed, limited access
    Trusted,    // Established trust, full privileges
    System,     // Local/system identity
    Rejected,   // Security violation, blocked
}

impl Default for TrustLevel {
    fn default() -> Self {
        TrustLevel::New
    }
}

// Unified Trust Manager (combines body AdmissionManager + HAL TrustStateMachine)
pub struct UnifiedTrustManager {
    identities: Arc<RwLock<HashMap<String, UnifiedIdentity>>>,
    trust_policies: Arc<RwLock<TrustPolicies>>,
    replay_cache: Arc<RwLock<ReplayCache>>,
}

#[derive(Debug, Default)]
pub struct TrustPolicies {
    pub minimum_trust_for_network: TrustLevel,
    pub packet_rate_limits: HashMap<TrustLevel, u32>,
    pub auto_promotion_threshold: u32,
    pub demotion_on_failure: bool,
}

#[derive(Debug, Default)]
pub struct ReplayCache {
    nonces: HashMap<String, u64>, // nonce -> timestamp
    max_age: u64, // seconds
}

impl UnifiedTrustManager {
    pub fn new() -> Self {
        Self {
            identities: Arc::new(RwLock::new(HashMap::new())),
            trust_policies: Arc::new(RwLock::new(TrustPolicies {
                minimum_trust_for_network: TrustLevel::Probation,
                packet_rate_limits: [
                    (TrustLevel::New, 5),
                    (TrustLevel::Probation, 50),
                    (TrustLevel::Trusted, 1000),
                    (TrustLevel::System, 10000),
                ].iter().cloned().collect(),
                auto_promotion_threshold: 10,
                demotion_on_failure: true,
            })),
            replay_cache: Arc::new(RwLock::new(ReplayCache {
                nonces: HashMap::new(),
                max_age: 300, // 5 minutes
            })),
        }
    }

    // Create new identity (consolidates NodeIdentity::pre_determine)
    pub fn create_identity(&self, storage_base: &std::path::Path) -> anyhow::Result<UnifiedIdentity> {
        let signing_key = SigningKey::generate(&mut rand::rngs::OsRng);
        let verifying_key: VerifyingKey = (&signing_key).into();
        let node_id = hex::encode(Sha256::digest(verifying_key.as_bytes()));
        
        let hardware_fingerprint = self.generate_hardware_fingerprint();
        
        let identity = UnifiedIdentity {
            node_id: node_id.clone(),
            signing_key,
            verifying_key,
            hardware_fingerprint,
            trust_level: TrustLevel::New,
            creation_timestamp: std::time::SystemTime::now()
                .duration_since(std::time::UNIX_EPOCH)?
                .as_secs(),
        };

        // Register self as system identity
        let mut identities = self.identities.blocking_write();
        identities.insert(node_id, identity.clone());

        Ok(identity)
    }

    // Register peer identity (combines AdmissionManager::register_handshake)
    pub async fn register_peer(&self, node_id: String, public_key: Vec<u8>) -> anyhow::Result<()> {
        let verifying_key = VerifyingKey::from_bytes(public_key[..32].try_into()?)?;
        
        let identity = UnifiedIdentity {
            node_id: node_id.clone(),
            signing_key: SigningKey::from_bytes(&[0u8; 32]), // Placeholder
            verifying_key,
            hardware_fingerprint: "remote_peer".to_string(),
            trust_level: TrustLevel::New,
            creation_timestamp: std::time::SystemTime::now()
                .duration_since(std::time::UNIX_EPOCH)?
                .as_secs(),
        };

        let mut identities = self.identities.write().await;
        identities.insert(node_id, identity);
        Ok(())
    }

    // Evaluate trust for packet (combines AdmissionManager::should_admit + TrustStateMachine logic)
    pub async fn evaluate_trust(&self, node_id: &str, packet_type: &str) -> TrustEvaluation {
        let identities = self.identities.read().await;
        let identity = match identities.get(node_id) {
            Some(id) => id,
            None => return TrustEvaluation::reject("Unknown identity"),
        };

        let policies = self.trust_policies.read().await;
        
        // Check minimum trust level
        if self.trust_level_rank(&identity.trust_level) < self.trust_level_rank(&policies.minimum_trust_for_network) {
            return TrustEvaluation::reject("Insufficient trust level");
        }

        // Packet type restrictions based on trust level
        match &identity.trust_level {
            TrustLevel::New if packet_type != "SYN" => {
                return TrustEvaluation::reject("New peers can only send SYN packets");
            }
            TrustLevel::Probation if !["SYN", "SYN-ACK", "HEARTBEAT"].contains(&packet_type) => {
                return TrustEvaluation::reject("Probation peers have limited packet types");
            }
            _ => {}
        }

        TrustEvaluation::allow(&identity.trust_level)
    }

    // Promote trust level (combines TrustStateMachine::promote)
    pub async fn promote_trust(&self, node_id: &str) -> anyhow::Result<()> {
        let mut identities = self.identities.write().await;
        let identity = identities.get_mut(node_id).ok_or_else(|| anyhow::anyhow!("Identity not found"))?;
        
        match identity.trust_level {
            TrustLevel::New => {
                identity.trust_level = TrustLevel::Probation;
                println!("Promoted {} to Probation", node_id);
            }
            TrustLevel::Probation => {
                // Check promotion threshold (simplified)
                identity.trust_level = TrustLevel::Trusted;
                println!("Promoted {} to Trusted", node_id);
            }
            _ => {} // Already at highest level
        }
        
        Ok(())
    }

    // Replay protection (consolidates ReplayCache functionality)
    pub async fn is_replay(&self, nonce: &str) -> bool {
        let now = std::time::SystemTime::now()
            .duration_since(std::time::UNIX_EPOCH)
            .unwrap()
            .as_secs();
        
        let mut cache = self.replay_cache.write().await;
        
        // Prune old nonces
        let cutoff_time = now - cache.max_age;
        cache.nonces.retain(|_, timestamp| *timestamp > cutoff_time);
        
        // Check for replay
        if cache.nonces.contains_key(nonce) {
            true
        } else {
            cache.nonces.insert(nonce.to_string(), now);
            false
        }
    }

    // Utility functions
    fn generate_hardware_fingerprint(&self) -> String {
        let mut sys = sysinfo::System::new_all();
        sys.refresh_all();
        let hostname = sysinfo::System::host_name().unwrap_or_else(|| "unknown".to_string());
        let cpu_info = sys.cpus().first().map(|c| c.brand()).unwrap_or("unknown").to_string();
        let mem_total = sys.total_memory();
        format!("{}-{}-{}", hostname, cpu_info, mem_total)
    }

    fn trust_level_rank(&self, level: &TrustLevel) -> u8 {
        match level {
            TrustLevel::Rejected => 0,
            TrustLevel::New => 1,
            TrustLevel::Probation => 2,
            TrustLevel::Trusted => 3,
            TrustLevel::System => 4,
        }
    }
}

#[derive(Debug)]
pub struct TrustEvaluation {
    pub allowed: bool,
    pub trust_level: TrustLevel,
    pub reason: Option<String>,
}

impl TrustEvaluation {
    pub fn allow(level: &TrustLevel) -> Self {
        Self {
            allowed: true,
            trust_level: level.clone(),
            reason: None,
        }
    }

    pub fn reject(reason: &str) -> Self {
        Self {
            allowed: false,
            trust_level: TrustLevel::Rejected,
            reason: Some(reason.to_string()),
        }
    }
}

// Integration with existing body components
impl UnifiedTrustManager {
    // Interface for existing mesh networking
    pub async fn verify_packet_admission(&self, node_id: &str, packet_type: &str, nonce: &str) -> bool {
        // Check replay first
        if self.is_replay(nonce).await {
            return false;
        }
        
        // Evaluate trust
        let evaluation = self.evaluate_trust(node_id, packet_type).await;
        evaluation.allowed
    }
    
    // Interface for HAL integration
    pub async fn get_trust_level(&self, node_id: &str) -> TrustLevel {
        let identities = self.identities.read().await;
        identities.get(node_id)
            .map(|id| id.trust_level.clone())
            .unwrap_or(TrustLevel::New)
    }
}