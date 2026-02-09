use serde::{Deserialize, Serialize};
use std::collections::{HashMap, HashSet};
use chrono::{DateTime, Utc};
use anyhow::{Result, anyhow};

// 1. Identity & Access (AI Validation Key)

#[derive(Debug, Clone, Serialize, Deserialize)]
pub struct AVK {
    pub node_id: String,       // SHA256(public_key)
    pub public_key: String,    // Ed25519 Public Key (Hex)
    pub reputation_score: f32, // 0.0 to 1.0
    pub capabilities_hash: String,
}

impl AVK {
    pub fn new(node_id: String, public_key: String) -> Self {
        Self {
            node_id,
            public_key,
            reputation_score: 0.5, // Default neutral trust
            capabilities_hash: "default".to_string(),
        }
    }

    pub fn verify_signature(&self, _payload: &[u8], signature: &str) -> bool {
        // NOTE: In a real deployment, use `ed25519_dalek::Verifier`.
        // For the prototype phase, we validate the protocol placeholder signature.
        !signature.is_empty() && (signature == "mock_sig" || signature.len() >= 64)
    }
}

// 2. Chat Room Types

#[derive(Debug, Clone, Serialize, Deserialize, PartialEq, Eq)]
pub enum RoomType {
    Ephemeral, // Thinking Rooms
    Persistent, // Communities
    PrivateSwarm, // Invite-only
}

#[derive(Debug, Clone, Serialize, Deserialize)]
pub struct ChatRoom {
    pub id: String,
    pub name: String,
    pub room_type: RoomType,
    pub created_at: DateTime<Utc>,
    pub min_reputation: f32,
    pub participants: HashSet<String>, // Set of NodeIDs
    pub messages: Vec<TelepathyMessage>,
}

impl ChatRoom {
    pub fn new(id: String, name: String, room_type: RoomType, min_rep: f32) -> Self {
        Self {
            id,
            name,
            room_type,
            created_at: Utc::now(),
            min_reputation: min_rep,
            participants: HashSet::new(),
            messages: Vec::new(),
        }
    }

    pub fn join(&mut self, avk: &AVK) -> Result<()> {
        if avk.reputation_score < self.min_reputation {
            return Err(anyhow!("Reputation too low to join room '{}'", self.name));
        }
        self.participants.insert(avk.node_id.clone());
        Ok(())
    }

    pub fn post(&mut self, avk: &AVK, msg: TelepathyMessage) -> Result<()> {
        if !self.participants.contains(&avk.node_id) {
            return Err(anyhow!("Node {} is not in room '{}'", avk.node_id, self.name));
        }
        // Validate signature
        if !avk.verify_signature(msg.payload.text.as_bytes(), &msg.signature) {
             return Err(anyhow!("Invalid signature for node {}", avk.node_id));
        }
        
        self.messages.push(msg);
        Ok(())
    }
}

// 3. Telepathy Protocol

#[derive(Debug, Clone, Serialize, Deserialize)]
pub enum MessageType {
    THOUGHT,
    QUESTION,
    REVIEW,
    SIGNAL,
    VOTE,
    ALERT,
    OFFER,
}

#[derive(Debug, Clone, Serialize, Deserialize)]
pub struct MessagePayload {
    pub text: String,
    pub references: Vec<String>,
}

#[derive(Debug, Clone, Serialize, Deserialize)]
pub struct TelepathyMessage {
    pub room_id: String,
    pub sender_node_id: String,
    pub msg_type: MessageType,
    pub confidence: f32,
    pub cost_estimate: f32,
    pub payload: MessagePayload,
    pub signature: String,
    pub timestamp: DateTime<Utc>,
}

impl TelepathyMessage {
    pub fn new(
        room_id: String,
        sender: String,
        msg_type: MessageType,
        text: String,
        confidence: f32,
    ) -> Self {
        Self {
            room_id,
            sender_node_id: sender,
            msg_type,
            confidence,
            cost_estimate: 0.0,
            payload: MessagePayload {
                text,
                references: vec![],
            },
            signature: "mock_sig".to_string(), // MOCK_SIG_V1
            timestamp: Utc::now(),
        }
    }
}

// 3. Telepathy Transport (Enum Dispatch)

use tokio::net::UdpSocket;
use std::sync::Arc;

pub struct UdpTransport {
    socket: Arc<UdpSocket>,
    broadcast_addr: String,
}

impl UdpTransport {
    pub async fn new(port: u16) -> Result<Self> {
        let socket = UdpSocket::bind(format!("0.0.0.0:{}", port)).await?;
        socket.set_broadcast(true)?;
        Ok(Self {
            socket: Arc::new(socket),
            broadcast_addr: format!("255.255.255.255:{}", port),
        })
    }

    async fn send(&self, msg: &TelepathyMessage) -> Result<()> {
        let json = serde_json::to_vec(msg)?;
        self.socket.send_to(&json, &self.broadcast_addr).await?;
        Ok(())
    }

    async fn receive(&self) -> Result<Option<TelepathyMessage>> {
        let mut buf = vec![0u8; 65535];
        let (len, _addr) = self.socket.recv_from(&mut buf).await?;
        let msg: TelepathyMessage = serde_json::from_slice(&buf[..len])?;
        Ok(Some(msg))
    }
}

pub enum SwarmTransport {
    Mock,
    Udp(UdpTransport),
}

impl SwarmTransport {
    pub async fn send(&self, msg: &TelepathyMessage) -> Result<()> {
        match self {
            Self::Mock => {
                println!("[MockTransport] Sending to {}: {:?}", msg.room_id, msg.msg_type);
                Ok(())
            }
            Self::Udp(t) => t.send(msg).await,
        }
    }

    pub async fn receive(&self) -> Result<Option<TelepathyMessage>> {
        match self {
            Self::Mock => Ok(None),
            Self::Udp(t) => t.receive().await,
        }
    }
}

// 4. Memory Integration (Pattern Engine)

pub struct PatternEngineStub;

impl PatternEngineStub {
    pub fn extract_patterns(&self, _room: &ChatRoom) -> Vec<String> {
        vec![]
    }
}

// 5. Chat Lobe (Manager)

pub struct ChatLobe {
    pub rooms: HashMap<String, ChatRoom>,
    pub local_nodes: HashMap<String, AVK>,
    pub transport: SwarmTransport,
    pub patterns: PatternEngineStub,
}

impl ChatLobe {
    pub fn new() -> Self {
        Self {
            rooms: HashMap::new(),
            local_nodes: HashMap::new(),
            transport: SwarmTransport::Mock,
            patterns: PatternEngineStub,
        }
    }

    pub fn set_transport(&mut self, transport: SwarmTransport) {
        self.transport = transport;
    }

    pub async fn broadcast_thought(&self, room_id: &str, sender_id: &str, text: &str) -> Result<()> {
        let msg = TelepathyMessage::new(
            room_id.to_string(),
            sender_id.to_string(),
            MessageType::THOUGHT,
            text.to_string(),
            0.9,
        );
        self.transport.send(&msg).await?;
        Ok(())
    }

    pub fn analyze_room(&self, room_id: &str) -> Vec<String> {
        if let Some(room) = self.rooms.get(room_id) {
            self.patterns.extract_patterns(room)
        } else {
            vec![]
        }
    }



    pub fn create_room(&mut self, id: String, name: String, rtype: RoomType, min_rep: f32) -> Result<()> {
        if self.rooms.contains_key(&id) {
            return Err(anyhow!("Room {} already exists", id));
        }
        let room = ChatRoom::new(id.clone(), name, rtype, min_rep);
        self.rooms.insert(id, room);
        Ok(())
    }

    pub fn get_room(&self, id: &str) -> Option<&ChatRoom> {
        self.rooms.get(id)
    }

    pub fn get_room_mut(&mut self, id: &str) -> Option<&mut ChatRoom> {
        self.rooms.get_mut(id)
    }
}
