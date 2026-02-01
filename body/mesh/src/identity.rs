//! Identity management and hardware binding
//! Implements PRD 10: Identity Continuity

use serde::{Deserialize, Serialize};
use sha2::{Sha256, Digest};
use std::path::Path;
use std::fs::File;
use std::io::{Read, Write};
use anyhow::{Result, anyhow};
use crate::crypto::{NodeSecrets, NodeIdentity};
#[cfg(target_family = "unix")]
use std::os::unix::fs::PermissionsExt;

/// Binds identity to hardware traits to prevent cloning
#[derive(Debug, Clone, Serialize, Deserialize, PartialEq)]
pub struct HardwareFingerprint {
    /// CPU Architecture
    pub cpu_arch: String,
    /// CPU Cores
    pub cpu_cores: u32,
    /// OS Type
    pub os_type: String,
    /// OS Release
    pub os_release: String,
    /// Hostname
    pub hostname: String,
    /// Total Memory (rounded to GB to avoid jitter)
    pub memory_gb: u32,
}

impl HardwareFingerprint {
    /// Generate a fingerprint of the current hardware
    pub fn current() -> Result<Self> {
        let cpu_num = sys_info::cpu_num().unwrap_or(1);
        let os_type = sys_info::os_type().unwrap_or_else(|_| "unknown".into());
        let os_release = sys_info::os_release().unwrap_or_else(|_| "unknown".into());
        let hostname = sys_info::hostname().unwrap_or_else(|_| "unknown".into());
        let mem = sys_info::mem_info().map(|m| m.total).unwrap_or(0);
        let memory_gb = (mem as f64 / 1024.0 / 1024.0).round() as u32;

        Ok(Self {
            cpu_arch: std::env::consts::ARCH.to_string(),
            cpu_cores: cpu_num,
            os_type,
            os_release,
            hostname,
            memory_gb,
        })
    }

    /// Calculate SHA256 hash of the fingerprint
    pub fn hash(&self) -> String {
        let mut hasher = Sha256::new();
        let json = serde_json::to_string(&self).unwrap();
        hasher.update(json.as_bytes());
        hex::encode(hasher.finalize())
    }
}

/// A persisted identity bound to hardware
#[derive(Serialize, Deserialize)]
pub struct PersistentIdentity {
    /// The public identity
    pub identity: NodeIdentity,
    /// Hardware seal (hash of fingerprint at time of creation)
    pub hardware_seal: String,
    /// The secret key material (serialized)
    #[serde(with = "hex_bytes")]
    pub secret_bytes: Vec<u8>,
    /// Creation time
    pub created_at: chrono::DateTime<chrono::Utc>,
}

impl PersistentIdentity {
    /// Create a new identity and bind to current hardware
    pub fn new(role: &str, name: &str) -> Result<Self> {
        let secrets = NodeSecrets::generate();
        let identity = secrets.identity(name, role);
        let fingerprint = HardwareFingerprint::current()?;
        
        Ok(Self {
            identity,
            hardware_seal: fingerprint.hash(),
            secret_bytes: secrets.to_bytes(),
            created_at: chrono::Utc::now(),
        })
    }

    /// Load from disk and verify hardware binding
    pub fn load_and_verify(path: &Path) -> Result<Self> {
        let mut file = File::open(path)?;
        let mut json = String::new();
        file.read_to_string(&mut json)?;
        
        let persisted: Self = serde_json::from_str(&json)?;
        
        // Verify hardware binding
        let current_fp = HardwareFingerprint::current()?;
        let current_hash = current_fp.hash();
        
        if persisted.hardware_seal != current_hash {
            return Err(anyhow!(
                "Hardware mismatch! Identity is bound to {:?}, but running on {:?}",
                persisted.hardware_seal, current_hash
            ));
        }

        Ok(persisted)
    }

    /// Save to disk with strict permissions
    pub fn save(&self, path: &Path) -> Result<()> {
        let json = serde_json::to_string_pretty(&self)?;
        
        if let Some(parent) = path.parent() {
            std::fs::create_dir_all(parent)?;
        }

        let mut file = File::create(path)?;
        
        // Set permissions to 0600 (Read/Write for owner only) on Unix
        #[cfg(target_family = "unix")]
        {
            let mut perms = file.metadata()?.permissions();
            perms.set_mode(0o600);
            file.set_permissions(perms)?;
        }

        file.write_all(json.as_bytes())?;
        Ok(())
    }

    /// Reconstruct NodeSecrets
    pub fn secrets(&self) -> Result<NodeSecrets> {
        NodeSecrets::from_bytes(&self.secret_bytes)
    }
}

// Helper for hex serialization
mod hex_bytes {
    use serde::{Deserialize, Deserializer, Serializer};
    
    pub fn serialize<S: Serializer>(bytes: &[u8], s: S) -> Result<S::Ok, S::Error> {
        s.serialize_str(&hex::encode(bytes))
    }
    
    pub fn deserialize<'de, D: Deserializer<'de>>(d: D) -> Result<Vec<u8>, D::Error> {
        let s = String::deserialize(d)?;
        hex::decode(&s).map_err(serde::de::Error::custom)
    }
}


/// Main Entry Point: Sovereignty Bootloader
/// 
/// 1. Scans `data/nodes/` for any existing identity.
/// 2. If found, verifies hardware seal. Pannics if mismatch.
/// 3. If none, generates new Identity, calculates NodeID, creates `data/nodes/<NodeID>/data`, and saves.
/// 4. Returns the verified `PersistentIdentity` and its root path.
pub fn load_or_create_identity(base_dir: &Path, role: &str, name: &str) -> Result<(PersistentIdentity, std::path::PathBuf)> {
    let nodes_dir = base_dir.join("nodes");
    
    // 1. Scan for existing nodes
    if nodes_dir.exists() {
        for entry in std::fs::read_dir(&nodes_dir)? {
            let entry = entry?;
            let path = entry.path();
            if path.is_dir() {
                // Check for identity.key inside
                let key_path = path.join("data").join("identity.key");
                if key_path.exists() {
                    println!("Found existing node identity at {:?}", key_path);
                    let identity = PersistentIdentity::load_and_verify(&key_path)?;
                    println!("Hardware Binding Verified. Identity: {}", identity.identity.id);
                    return Ok((identity, path));
                }
            }
        }
    }

    // 2. No identity found. Genesis sequence.
    println!("No existing identity found. Initiating Genesis Sequence...");
    
    let new_identity = PersistentIdentity::new(role, name)?;
    let node_id = &new_identity.identity.id;
    
    // define sovereign root: data/nodes/<NodeID>/
    let node_root = nodes_dir.join(node_id);
    let data_dir = node_root.join("data");
    let key_path = data_dir.join("identity.key");
    
    // 3. Persist with strict permissions (0600)
    new_identity.save(&key_path)?;
    
    println!("Genesis Complete. Sovereign Node Created: {}", node_id);
    println!("Root: {:?}", node_root);
    
    Ok((new_identity, node_root))
}
