
//! Economy Module - The Metabolic Core of IPPOC
//! Implements PRD 14: Sovereign Swarm Spec (Metabolism)

use serde::{Deserialize, Serialize};
use std::path::PathBuf;
use anyhow::{Result, anyhow};
use chrono::Utc;
use sha2::{Sha256, Digest};

/// 3-Layer Currency Model
#[derive(Debug, Clone, Serialize, Deserialize, PartialEq, Default)]
pub struct Balances {
    /// L0: Internal Cognitive Fuel (Compute, Reasoning)
    pub ippc: u128,
    /// L1: Stable Accounting (Budgets, Salaries)
    pub iusd: u128,
    /// L2: Settlement & Governance Power (Virtual representation of on-chain)
    pub eth_virtual: u128,
}


/// Types of economic actions
#[derive(Debug, Clone, Serialize, Deserialize, PartialEq)]
pub enum ActionType {
    LlmInference { tokens: u32, model: String },
    ToolExecution { tool: String },
    EvolutionSim { pr_id: String },
    BountyPayout { target: String },
    DaoFee,
    Transfer { target: String },
    SystemGrant, // Genesis minting
    DecayBurn { amount: u128 }, // Entropy
    Vote { proposal_id: String, vote: bool },
}

/// DAO Governance Proposal Types (Layer 4)
#[derive(Debug, Clone, Serialize, Deserialize, PartialEq)]
pub enum ProposalType {
    AdjustCosts { action: String, new_cost: u128 },
    FundNode { node_id: String, amount: u128 },
    SlashNode { node_id: String, reason: String },
    ApproveEvolution { commit_hash: String },
    EmergencyFreeze,
}

/// Outcome of an action
#[derive(Debug, Clone, Serialize, Deserialize, PartialEq)]
pub enum Outcome {
    Pending,
    Success,
    Fail,
}

/// Verification Proof for Ledger Entry
#[derive(Debug, Clone, Serialize, Deserialize)]
pub struct Proof {
    pub signature: String, // Ed25519 hex
    pub signer: String,    // NodeID
}

/// Canonical Source of Truth
#[derive(Debug, Clone, Serialize, Deserialize)]
pub struct LedgerEntry {
    /// Monotonic Sequence Number (Layer 2 Hardening)
    pub seq_no: u64,
    /// SHA256(prev_hash + data)
    pub tx_id: String,
    pub timestamp: u64,
    pub actor: String,
    /// Economic Ruleset Version
    pub policy_version: String,
    pub action: ActionType,
    pub debit: Balances,
    pub credit: Balances,
    pub outcome: Outcome,
    pub proof: Option<Proof>,
    /// Hash of the previous entry for immutability
    pub prev_hash: String,
}

/// The Metabolic Controller
pub struct EconomyController {
    /// Persist Path
    db_path: PathBuf,
    /// In-memory wallet state
    pub wallet: Wallet,
    /// Append-only log
    ledger: Vec<LedgerEntry>,
    /// Current Policy Version
    policy_version: String,
}

#[derive(Debug, Clone, Serialize, Deserialize)]
pub struct Wallet {
    pub node_id: String,
    pub balances: Balances,
    pub reputation: f32,
    pub locked: bool,
    pub last_updated: u64,
}

impl EconomyController {
    /// Initialize the Economy for this Node
    pub fn new(node_id: &str, node_root: &std::path::Path) -> Result<Self> {
        let economy_dir = node_root.join("economy");
        std::fs::create_dir_all(&economy_dir)?;
        
        let ledger_path = economy_dir.join("ledger.json");
        let wallet_path = economy_dir.join("wallet.json");

        let wallet = if wallet_path.exists() {
            let data = std::fs::read_to_string(&wallet_path)?;
            serde_json::from_str(&data)?
        } else {
            // Genesis Wallet (Empty)
            Wallet {
                node_id: node_id.to_string(),
                balances: Balances::default(),
                reputation: 10.0, // Base rep
                locked: false,
                last_updated: Utc::now().timestamp() as u64,
            }
        };

        let ledger = if ledger_path.exists() {
            let data = std::fs::read_to_string(&ledger_path)?;
            serde_json::from_str(&data)?
        } else {
            Vec::new()
        };

        Ok(Self {
            db_path: economy_dir,
            wallet,
            ledger,
            policy_version: "1.0.0".to_string(),
        })
    }

    /// Check if we can afford an action
    pub fn can_afford(&self, action: &ActionType) -> bool {
        let cost = self.estimate_cost(action);
        self.wallet.balances.ippc >= cost.ippc &&
        self.wallet.balances.iusd >= cost.iusd
    }

    /// Estimate cost of an action (Hardcoded Policy for now)
    pub fn estimate_cost(&self, action: &ActionType) -> Balances {
        match action {
            ActionType::LlmInference { tokens, .. } => Balances {
                ippc: 10 + (*tokens as u128 / 100), // Base + 1 per 100 tokens
                iusd: 0,
                eth_virtual: 0,
            },
            ActionType::ToolExecution { .. } => Balances {
                ippc: 50,
                iusd: 0,
                eth_virtual: 0,
            },
            ActionType::EvolutionSim { .. } => Balances {
                ippc: 500,
                iusd: 0,
                eth_virtual: 0,
            },
            ActionType::DaoFee => Balances {
                ippc: 0,
                iusd: 0,
                eth_virtual: 1000, 
            },
            ActionType::DecayBurn { amount } => Balances {
                ippc: *amount,
                iusd: 0,
                eth_virtual: 0,
            },
            _ => Balances::default(),
        }
    }

    /// Apply Entropy (Decay) to IPPC to prevent hoarding
    /// Humans get tired. Nodes leak energy.
    pub fn apply_decay(&mut self) -> Result<()> {
        let current_ippc = self.wallet.balances.ippc;
        if current_ippc > 100 {
            let decay_amount = current_ippc / 50; // 2% decay
            if decay_amount > 0 {
                let node_id = self.wallet.node_id.clone();
                self.record_action(
                    &node_id,
                    ActionType::DecayBurn { amount: decay_amount },
                    Outcome::Success
                )?;
            }
        }
        Ok(())
    }

    /// Execute a transaction (Append to Ledger + Update Wallet)
    pub fn record_action(&mut self, actor: &str, action: ActionType, outcome: Outcome) -> Result<()> {
        let cost = self.estimate_cost(&action);
        
        // Check Funds
        if outcome == Outcome::Success && self.wallet.balances.ippc < cost.ippc {
             return Err(anyhow!("Insufficient IPPC Funds"));
        }

        // Create Ledger Entry
        let prev_hash = self.ledger.last()
            .map(|e| e.tx_id.clone())
            .unwrap_or_else(|| "0000000000000000000000000000000000000000000000000000000000000000".to_string());
        
        let seq_no = self.ledger.last().map(|e| e.seq_no + 1).unwrap_or(0);
        let timestamp = Utc::now().timestamp() as u64;
        
        // Calculate hash
        let mut hasher = Sha256::new();
        hasher.update(&prev_hash);
        hasher.update(actor.as_bytes());
        hasher.update(timestamp.to_be_bytes());
        hasher.update(seq_no.to_be_bytes()); // Include seq_no in hash
        let tx_id = hex::encode(hasher.finalize());

        let entry = LedgerEntry {
            seq_no,
            tx_id,
            timestamp,
            actor: actor.to_string(),
            policy_version: self.policy_version.clone(),
            action,
            debit: cost.clone(), 
            credit: Balances::default(),
            outcome: outcome.clone(),
            proof: None, 
            prev_hash,
        };

        // Update Wallet State
        if outcome == Outcome::Success {
            self.wallet.balances.ippc -= cost.ippc;
            self.wallet.balances.iusd -= cost.iusd;
            self.wallet.last_updated = timestamp;
        }

        self.ledger.push(entry);
        self.save()?;
        
        Ok(())
    }

    /// Grant funds (System / Genesis / Reward)
    pub fn grant(&mut self, amount: Balances, _reason: &str) -> Result<()> {
        let node_id = self.wallet.node_id.clone();
        
        self.wallet.balances.ippc += amount.ippc;
        self.wallet.balances.iusd += amount.iusd;
        self.wallet.balances.eth_virtual += amount.eth_virtual;
        
        self.record_action(
            &node_id, 
            ActionType::SystemGrant, 
            Outcome::Success
        )?;
        Ok(())
    }

    fn save(&self) -> Result<()> {
        let wallet_json = serde_json::to_string_pretty(&self.wallet)?;
        let ledger_json = serde_json::to_string_pretty(&self.ledger)?;
        
        std::fs::write(self.db_path.join("wallet.json"), wallet_json)?;
        std::fs::write(self.db_path.join("ledger.json"), ledger_json)?;
        
        Ok(())
    }
}
