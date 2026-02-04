//! IPPOC - Integrated Persistent Programmable Organism Core
//! 
//! A cognitive computing system with biological-inspired architecture
//! featuring temporal-causal memory, reputation-weighted economics,
//! and evolutionary policy enforcement.

pub mod core;
pub mod network;
pub mod memory;
pub mod cognition;
pub mod economy;
pub mod evolution;
pub mod security;

/// Main IPPOC system entry point
pub struct IPPOC {
    pub network: network::mesh::AiMesh,
    pub memory: memory::hidb::HiDB,
    pub brain: cognition::cerebellum::Cerebrum,
    pub economy: economy::rwe::RWE,
}

impl IPPOC {
    /// Initialize the complete IPPOC system
    pub async fn new() -> Result<Self, anyhow::Error> {
        // Initialize core components
        let network = network::mesh::AiMesh::new(network::mesh::MeshConfig::default()).0;
        let memory = memory::hidb::init("postgresql://localhost/ippoc", "redis://localhost").await?;
        let brain = cognition::cerebellum::Cerebrum::new(memory.clone());
        let economy = economy::rwe::RWE::new(1000.0); // Base budget
        
        Ok(Self {
            network,
            memory,
            brain,
            economy,
        })
    }
    
    /// Start all system components
    pub async fn start(&self) -> Result<(), anyhow::Error> {
        self.network.start_networking().await?;
        Ok(())
    }
}