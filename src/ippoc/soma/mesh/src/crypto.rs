//! Cryptographic primitives for AI node communication
//! Based on BitChat's security model: X25519 + AES-256-GCM + Ed25519

use aes_gcm::{Aes256Gcm, Key, Nonce};
use aes_gcm::aead::{Aead, KeyInit};
use anyhow::{Result, anyhow};
use ed25519_dalek::{SigningKey, VerifyingKey, Signature, Signer, Verifier};
use hkdf::Hkdf;
use rand::rngs::OsRng;
use sha2::{Sha256, Digest};
use x25519_dalek::{PublicKey, StaticSecret};
use serde::{Deserialize, Serialize};

/// Unique identity for an AI node
#[derive(Debug, Clone, Serialize, Deserialize)]
pub struct NodeIdentity {
    /// Node's unique ID (SHA256 hash of public key)
    pub id: String,
    /// Public key for key exchange (X25519)
    #[serde(with = "hex_bytes")]
    pub exchange_public: [u8; 32],
    /// Public key for signing (Ed25519)
    #[serde(with = "hex_bytes")]
    pub signing_public: [u8; 32],
    /// Node role
    pub role: String,
    /// Human-readable name
    pub name: String,
}

/// Node's secret keys (never shared)
pub struct NodeSecrets {
    /// Static secret for key exchange
    exchange_secret: StaticSecret,
    /// Signing key
    signing_key: SigningKey,
}

impl NodeSecrets {
    /// Generate new node secrets
    pub fn generate() -> Self {
        Self {
            exchange_secret: StaticSecret::random_from_rng(OsRng),
            signing_key: SigningKey::generate(&mut OsRng),
        }
    }

    /// Get public identity
    pub fn identity(&self, name: &str, role: &str) -> NodeIdentity {
        let exchange_public = PublicKey::from(&self.exchange_secret);
        let signing_public = self.signing_key.verifying_key();
        let id = hex::encode(sha2::Sha256::digest(signing_public.as_bytes()));
        
        NodeIdentity {
            id,
            exchange_public: exchange_public.to_bytes(),
            signing_public: signing_public.to_bytes(),
            role: role.to_string(),
            name: name.to_string(),
        }
    }

    /// Derive shared secret with peer
    pub fn derive_shared(&self, peer_public: &[u8; 32]) -> SharedSecret {
        let peer_key = PublicKey::from(*peer_public);
        let raw_shared = self.exchange_secret.diffie_hellman(&peer_key);
        
        // Derive encryption key using HKDF
        let hk = Hkdf::<Sha256>::new(None, raw_shared.as_bytes());
        let mut encryption_key = [0u8; 32];
        hk.expand(b"ippoc-ai-mesh-v1", &mut encryption_key)
            .expect("HKDF expand failed");
        
        SharedSecret { key: encryption_key }
    }

    /// Sign a message
    pub fn sign(&self, message: &[u8]) -> [u8; 64] {
        self.signing_key.sign(message).to_bytes()
    }

    /// Serialize secrets to bytes
    pub fn to_bytes(&self) -> Vec<u8> {
        let mut bytes = Vec::new();
        // Exchange secret (32 bytes)
        bytes.extend_from_slice(&self.exchange_secret.to_bytes());
        // Signing key bytes (32 bytes seed)
        bytes.extend_from_slice(&self.signing_key.to_bytes());
        bytes
    }

    /// Deserialize secrets from bytes
    pub fn from_bytes(bytes: &[u8]) -> Result<Self> {
        if bytes.len() != 64 {
            return Err(anyhow!("Invalid secrets length: expected 64, got {}", bytes.len()));
        }
        
        let exchange_bytes: [u8; 32] = bytes[0..32].try_into()?;
        let signing_bytes: [u8; 32] = bytes[32..64].try_into()?;
        
        Ok(Self {
            exchange_secret: StaticSecret::from(exchange_bytes),
            signing_key: SigningKey::from_bytes(&signing_bytes),
        })
    }
}

/// Shared secret for encrypted communication
#[derive(Clone)]
pub struct SharedSecret {
    key: [u8; 32],
}

impl SharedSecret {
    /// Get key bytes
    pub fn as_bytes(&self) -> &[u8; 32] {
        &self.key
    }
}

/// Encrypt a message using AES-256-GCM
pub fn encrypt_message(shared: &SharedSecret, plaintext: &[u8]) -> Result<Vec<u8>> {
    let key = Key::<Aes256Gcm>::from_slice(&shared.key);
    let cipher = Aes256Gcm::new(key);
    
    // Generate random nonce
    let mut nonce_bytes = [0u8; 12];
    getrandom::getrandom(&mut nonce_bytes)?;
    let nonce = Nonce::from_slice(&nonce_bytes);
    
    let ciphertext = cipher.encrypt(nonce, plaintext)
        .map_err(|e| anyhow!("Encryption failed: {e}"))?;
    
    // Prepend nonce to ciphertext
    let mut result = nonce_bytes.to_vec();
    result.extend(ciphertext);
    
    Ok(result)
}

/// Decrypt a message using AES-256-GCM
pub fn decrypt_message(shared: &SharedSecret, encrypted: &[u8]) -> Result<Vec<u8>> {
    if encrypted.len() < 12 {
        return Err(anyhow!("Invalid encrypted message: too short"));
    }
    
    let key = Key::<Aes256Gcm>::from_slice(&shared.key);
    let cipher = Aes256Gcm::new(key);
    
    let (nonce_bytes, ciphertext) = encrypted.split_at(12);
    let nonce = Nonce::from_slice(nonce_bytes);
    
    let plaintext = cipher.decrypt(nonce, ciphertext)
        .map_err(|e| anyhow!("Decryption failed: {e}"))?;
    
    Ok(plaintext)
}

/// Verify a signature
pub fn verify_signature(signing_public: &[u8; 32], message: &[u8], signature: &[u8; 64]) -> Result<bool> {
    let verifying_key = VerifyingKey::from_bytes(signing_public)
        .map_err(|e| anyhow!("Invalid public key: {e}"))?;
    let sig = Signature::from_bytes(signature);
    
    Ok(verifying_key.verify(message, &sig).is_ok())
}

// Helper for serializing byte arrays as hex
mod hex_bytes {
    use serde::{Deserialize, Deserializer, Serializer};
    
    pub fn serialize<S: Serializer>(bytes: &[u8; 32], s: S) -> Result<S::Ok, S::Error> {
        s.serialize_str(&hex::encode(bytes))
    }
    
    pub fn deserialize<'de, D: Deserializer<'de>>(d: D) -> Result<[u8; 32], D::Error> {
        let s = String::deserialize(d)?;
        let bytes = hex::decode(&s).map_err(serde::de::Error::custom)?;
        let mut arr = [0u8; 32];
        arr.copy_from_slice(&bytes);
        Ok(arr)
    }
}

#[cfg(test)]
mod tests {
    use super::*;
    
    #[test]
    fn test_key_exchange_and_encryption() {
        let alice = NodeSecrets::generate();
        let bob = NodeSecrets::generate();
        
        let alice_identity = alice.identity("alice", "reasoning");
        let bob_identity = bob.identity("bob", "retrieval");
        
        // Both derive the same shared secret
        let alice_shared = alice.derive_shared(&bob_identity.exchange_public);
        let bob_shared = bob.derive_shared(&alice_identity.exchange_public);
        
        assert_eq!(alice_shared.as_bytes(), bob_shared.as_bytes());
        
        // Encrypt/decrypt
        let message = b"Hello from Alice!";
        let encrypted = encrypt_message(&alice_shared, message).unwrap();
        let decrypted = decrypt_message(&bob_shared, &encrypted).unwrap();
        
        assert_eq!(message.as_slice(), decrypted.as_slice());
    }
}
