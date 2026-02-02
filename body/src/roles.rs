use sysinfo::System;
use serde::{Deserialize, Serialize};
use tracing::info;

#[derive(Debug, Clone, Serialize, Deserialize, PartialEq)]
pub enum NodeRole {
    Reasoning, // High GPU/CPU
    Retrieval, // High RAM/Disk
    Tool,      // Standard
    Relay,     // Low power
}

pub struct RoleManager {
    sys: System,
}

#[allow(dead_code)]
impl RoleManager {
    pub fn new() -> Self {
        Self {
            sys: System::new_all(),
        }
    }

    pub fn determine_role(&mut self) -> NodeRole {
        self.sys.refresh_all();

        let total_memory_gb = self.sys.total_memory() / 1024 / 1024 / 1024;
        let cpu_cores = self.sys.cpus().len();

        // Simple heuristic
        if total_memory_gb > 64 || cpu_cores > 16 {
            // Assume powerful machine -> Reasoning
            info!("Hardware Analysis: {}GB RAM, {} Cores -> Role: REASONING", total_memory_gb, cpu_cores);
            NodeRole::Reasoning
        } else if total_memory_gb > 32 {
            // Good memory -> Retrieval
            info!("Hardware Analysis: {}GB RAM, {} Cores -> Role: RETRIEVAL", total_memory_gb, cpu_cores);
            NodeRole::Retrieval
        } else {
            // Standard -> Tool
            info!("Hardware Analysis: {}GB RAM, {} Cores -> Role: TOOL", total_memory_gb, cpu_cores);
            NodeRole::Tool
        }
    }
}
