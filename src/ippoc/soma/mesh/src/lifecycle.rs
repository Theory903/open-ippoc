
//! Node Lifecycle - The Biological Clock of IPPOC Nodes
//! Implements NODE_LIFECYCLE.md

use serde::{Deserialize, Serialize};
use std::time::{SystemTime, UNIX_EPOCH};

#[derive(Debug, Clone, Copy, PartialEq, Eq, Serialize, Deserialize)]
pub enum NodeState {
    /// Just born. Limited capabilities.
    Newborn,
    /// Fully functional. Can earn and learn.
    Active,
    /// Under observation due to suspicious behavior.
    Probation,
    /// Governor status. Can vote and spawn.
    Trusted,
    /// Inactive due to lack of funds or tasks.
    Dormant,
    /// System detects failure/unresponsiveness.
    Dying,
    /// Gracefully retired. Code and Memory preserved.
    Archived,
    /// Punitive death. Assets seized.
    Slashed,
}

#[derive(Debug, Clone, Serialize, Deserialize)]
pub struct LifecycleState {
    pub current_state: NodeState,
    pub birth_timestamp: u64,
    pub last_active: u64,
    pub promotion_criteria_met: bool,
}

impl Default for LifecycleState {
    fn default() -> Self {
        Self {
            current_state: NodeState::Newborn,
            birth_timestamp: now(),
            last_active: now(),
            promotion_criteria_met: false,
        }
    }
}

impl Default for LifecycleManager {
    fn default() -> Self {
        Self::new()
    }
}

pub struct LifecycleManager {
    state: LifecycleState,
}

impl LifecycleManager {
    pub fn new() -> Self {
        Self { state: LifecycleState::default() }
    }

    /// Check if node can perform a specific high-level capability
    pub fn can_reason(&self) -> bool {
        matches!(self.state.current_state, NodeState::Active | NodeState::Trusted | NodeState::Probation)
    }

    pub fn can_vote(&self) -> bool {
        matches!(self.state.current_state, NodeState::Trusted)
    }

    pub fn can_spawn(&self) -> bool {
        matches!(self.state.current_state, NodeState::Trusted)
    }

    /// Update activity timestamp (Heartbeat)
    pub fn heartbeat(&mut self) {
        self.state.last_active = now();
        // Auto-recovery from Dormant if funded (logic to be connected to Economy)
        if self.state.current_state == NodeState::Dormant {
             // For now, simpler transition back
             self.state.current_state = NodeState::Active; 
        }
    }

    /// Attempt promotion from Newborn -> Active
    pub fn try_promote(&mut self, reputation: f32, balance: u128) {
        if self.state.current_state == NodeState::Newborn {
            // Criteria: 100 IPPC + positive rep
            if balance >= 100 && reputation > 0.0 {
                self.state.current_state = NodeState::Active;
            }
        }
    }

    /// Force state transition (System/DAO override)
    pub fn set_state(&mut self, new_state: NodeState) {
        self.state.current_state = new_state;
    }
    
    pub fn current(&self) -> NodeState {
        self.state.current_state
    }

    pub fn get_state(&self) -> LifecycleState {
        self.state.clone()
    }
}

fn now() -> u64 {
    SystemTime::now().duration_since(UNIX_EPOCH).unwrap().as_secs()
}
