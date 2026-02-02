use sysinfo::System;
use sha2::{Sha256, Digest};
use std::fs;
use std::path::Path;
use anyhow::Result;
use tracing::info;
use ed25519_dalek::{SigningKey, VerifyingKey};
use rand::rngs::OsRng;

pub struct NodeIdentity {
    #[allow(dead_code)]
    pub node_id: String,
    pub signing_key: SigningKey,
}

#[allow(dead_code)]
impl NodeIdentity {
    /// Determines the NodeID before the isolation root is finalized.
    /// Returns the NodeID and the key. Does NOT write to isolation root yet.
    pub fn pre_determine(storage_base: &Path) -> Result<(String, SigningKey)> {
        // Try to find an existing identity in the global registry or probe node dirs
        // For simplicity, we check a global sentinel or the first node dir.
        let global_key_path = storage_base.join("identity.master.key");

        let signing_key = if global_key_path.exists() {
            let key_bytes = fs::read(&global_key_path)?;
            let bytes: [u8; 32] = key_bytes.try_into().map_err(|_| anyhow::anyhow!("Invalid key"))?;
            SigningKey::from_bytes(&bytes)
        } else {
            info!("NodeIdentity: No existing master identity found. Generating fresh...");
            let key = SigningKey::generate(&mut OsRng);
            // We write a master sentinel to storage_base to ensure future boots find this ID
            fs::write(&global_key_path, key.to_bytes())?;
            
            #[cfg(unix)]
            {
                use std::os::unix::fs::PermissionsExt;
                fs::set_permissions(&global_key_path, fs::Permissions::from_mode(0o600))?;
            }
            key
        };

        let verifying_key: VerifyingKey = (&signing_key).into();
        let node_id = hex::encode(Sha256::digest(verifying_key.as_bytes()));

        info!("NodeIdentity: Pre-determined ID: {}", node_id);
        Ok((node_id, signing_key))
    }

    /// Persists the pre-determined identity into the NOW READY isolation root.
    pub fn persist(&self, isolation_root: &Path) -> Result<()> {
        let identity_dir = isolation_root.join("data");
        let key_path = identity_dir.join("identity.key");
        let fingerprint_path = identity_dir.join("hardware_fingerprint.json");

        if !key_path.exists() {
            fs::write(&key_path, self.signing_key.to_bytes())?;
            
            #[cfg(unix)]
            {
                use std::os::unix::fs::PermissionsExt;
                fs::set_permissions(&key_path, fs::Permissions::from_mode(0o600))?;
            }

            let mut sys = System::new_all();
            sys.refresh_all();
            let hostname = System::host_name().unwrap_or_else(|| "unknown".to_string());
            let cpu_info = sys.cpus().first().map(|c| c.brand()).unwrap_or("unknown").to_string();
            let mem_total = sys.total_memory();
            let fingerprint = format!("{hostname}-{cpu_info}-{mem_total}");
            fs::write(&fingerprint_path, fingerprint)?;
            
            info!("NodeIdentity: Identity persisted to isolation root and bound to hardware.");
        }
        Ok(())
    }
}
