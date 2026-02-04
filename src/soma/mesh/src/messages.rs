//! AI-to-AI Message Types
//! Defines the protocol for node communication

use serde::{Deserialize, Serialize};
use uuid::Uuid;
use chrono::{DateTime, Utc};

/// Types of messages in the AI mesh
#[derive(Debug, Clone, Serialize, Deserialize, PartialEq)]
pub enum MessageType {
    /// A thought to be processed by peers
    Thought,
    /// A broadcast to all nodes
    Broadcast,
    /// Direct message to specific node
    Direct,
    /// Node discovery/heartbeat
    Discovery,
    /// Request for collaboration
    CollaborationRequest,
    /// Response to a request
    Response,
    /// Memory sync request
    MemorySync,
    /// Tool invocation request
    ToolRequest,
    /// Evolution proposal
    EvolutionProposal,
    /// Handshake protocol
    Handshake,
}

/// LangChain-compatible Message Types (Strict Alignment)
#[derive(Debug, Clone, Serialize, Deserialize, PartialEq)]
#[serde(tag = "type")]
pub enum LcMessage {
    #[serde(rename = "human")]
    Human { content: String },
    
    #[serde(rename = "ai")]
    Ai { 
        content: String, 
        #[serde(default, skip_serializing_if = "Vec::is_empty")]
        tool_calls: Vec<LcToolCall> 
    },
    
    #[serde(rename = "system")]
    System { content: String },
    
    #[serde(rename = "tool")]
    Tool { content: String, tool_call_id: String },
}

#[derive(Debug, Clone, Serialize, Deserialize, PartialEq)]
pub struct LcToolCall {
    pub id: String,
    pub name: String,
    pub args: serde_json::Value,
    #[serde(rename = "type")]
    pub kind: String, // usually "tool_call" or "function"
}

/// Start of Handshake kinds
#[derive(Debug, Clone, Serialize, Deserialize, PartialEq)]
pub enum HandshakeKind {
    /// SYN (Initiation)
    Syn,
    /// SYN-ACK (Challenge/Response)
    SynAck,
    /// ACK (Finalization)
    Ack,
}

/// Handshake message for key exchange and authentication
#[derive(Debug, Clone, Serialize, Deserialize)]
pub struct HandshakeMessage {
    /// Handshake kind
    pub kind: HandshakeKind,
    /// Public key for exchange
    pub exchange_public: [u8; 32],
    /// Public key for signing
    pub signing_public: [u8; 32],
    /// Nonce for challenge/replay protection
    pub nonce: [u8; 16],
    /// Optional challenge (encrypted for SYN-ACK)
    pub challenge: Option<Vec<u8>>,
}

/// An AI thought to be shared across the mesh
#[derive(Debug, Clone, Serialize, Deserialize)]
pub struct Thought {
    /// Thought content (can be structured)
    pub content: serde_json::Value,
    /// Semantic embedding (optional)
    pub embedding: Option<Vec<f32>>,
    /// Confidence level (0.0-1.0)
    pub confidence: f32,
    /// Source context
    pub context: Option<String>,
    /// Tags for routing
    pub tags: Vec<String>,
}

/// A broadcast message to all nodes
#[derive(Debug, Clone, Serialize, Deserialize)]
pub struct Broadcast {
    /// Channel/topic
    pub channel: String,
    /// Content
    pub content: serde_json::Value,
    /// Priority (higher = more important)
    pub priority: u8,
    /// TTL in hops
    pub ttl: u8,
}

/// Complete AI message envelope
#[derive(Debug, Clone, Serialize, Deserialize)]
pub struct AiMessage {
    /// Unique message ID (Transient tracking only)
    pub id: Uuid,
    /// Message type
    pub msg_type: MessageType,
    /// Sender NodeID (Cryptographic String)
    pub sender: String,
    /// Recipient NodeID (None for broadcasts)
    pub recipient: Option<String>,
    /// Timestamp
    pub timestamp: DateTime<Utc>,
    /// Payload (encrypted content)
    pub payload: Vec<u8>,
    /// Signature of payload (as hex string for serialization)
    pub signature: String,
    /// Message sequence number (for ordering)
    pub sequence: u64,
    /// Nonce for replay protection
    pub nonce: u64,
    /// Optional reply-to message ID
    pub reply_to: Option<Uuid>,
}

impl AiMessage {
    /// Create a new thought message
    pub fn thought(sender: &str, thought: &Thought, sequence: u64) -> Self {
        let payload = serde_json::to_vec(thought).unwrap_or_default();
        Self {
            id: Uuid::new_v4(),
            msg_type: MessageType::Thought,
            sender: sender.to_string(),
            recipient: None,
            timestamp: Utc::now(),
            payload,
            signature: String::new(),
            sequence,
            nonce: rand::random(),
            reply_to: None,
        }
    }

    /// Create a new broadcast message
    pub fn broadcast(sender: &str, broadcast: &Broadcast, sequence: u64) -> Self {
        let payload = serde_json::to_vec(broadcast).unwrap_or_default();
        Self {
            id: Uuid::new_v4(),
            msg_type: MessageType::Broadcast,
            sender: sender.to_string(),
            recipient: None,
            timestamp: Utc::now(),
            payload,
            signature: String::new(),
            sequence,
            nonce: rand::random(),
            reply_to: None,
        }
    }

    /// Create a direct message
    pub fn direct(sender: &str, recipient: &str, content: serde_json::Value, sequence: u64) -> Self {
        let payload = serde_json::to_vec(&content).unwrap_or_default();
        Self {
            id: Uuid::new_v4(),
            msg_type: MessageType::Direct,
            sender: sender.to_string(),
            recipient: Some(recipient.to_string()),
            timestamp: Utc::now(),
            payload,
            signature: String::new(),
            sequence,
            nonce: rand::random(),
            reply_to: None,
        }
    }

    /// Create a discovery/heartbeat message
    pub fn discovery(sender: &str, node_info: serde_json::Value) -> Self {
        let payload = serde_json::to_vec(&node_info).unwrap_or_default();
        Self {
            id: Uuid::new_v4(),
            msg_type: MessageType::Discovery,
            sender: sender.to_string(),
            recipient: None,
            timestamp: Utc::now(),
            payload,
            signature: String::new(),
            sequence: 0,
            nonce: rand::random(),
            reply_to: None,
        }
    }

    /// Create a handshake message
    pub fn handshake(sender: &str, recipient: Option<&str>, hs: &HandshakeMessage) -> Self {
        let payload = serde_json::to_vec(hs).unwrap_or_default();
        Self {
            id: Uuid::new_v4(),
            msg_type: MessageType::Handshake,
            sender: sender.to_string(),
            recipient: recipient.map(|r| r.to_string()),
            timestamp: Utc::now(),
            payload,
            signature: String::new(),
            sequence: 0,
            nonce: rand::random(),
            reply_to: None,
        }
    }

    /// Serialize for transmission
    pub fn to_bytes(&self) -> Vec<u8> {
        bincode::serialize(self).unwrap_or_default()
    }

    /// Deserialize from bytes
    pub fn from_bytes(bytes: &[u8]) -> Option<Self> {
        bincode::deserialize(bytes).ok()
    }
}

/// Collaboration request between nodes
#[derive(Debug, Clone, Serialize, Deserialize)]
pub struct CollaborationRequest {
    /// Task description
    pub task: String,
    /// Required capabilities
    pub required_roles: Vec<String>,
    /// Deadline (optional)
    pub deadline: Option<DateTime<Utc>>,
    /// Priority
    pub priority: u8,
    /// Context/memory references
    pub context_refs: Vec<Uuid>,
}

/// Tool request message
#[derive(Debug, Clone, Serialize, Deserialize)]
pub struct ToolRequest {
    /// Tool name
    pub tool: String,
    /// Arguments
    pub args: serde_json::Value,
    /// Timeout in seconds
    pub timeout_secs: u32,
    /// Sandbox required
    pub sandboxed: bool,
}

/// Evolution proposal message
#[derive(Debug, Clone, Serialize, Deserialize)]
pub struct EvolutionProposal {
    /// Proposed change description
    pub description: String,
    /// Diff/patch content
    pub patch: String,
    /// Simulation results
    pub simulation_passed: bool,
    /// Votes required
    pub votes_required: u32,
    /// Current votes
    pub votes: Vec<Uuid>,
}
