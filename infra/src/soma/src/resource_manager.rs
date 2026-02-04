// Consolidated Resource Management System
// Merges body economy controller with HAL budgeting semantics

use std::collections::HashMap;
use std::sync::Arc;
use tokio::sync::RwLock;
use serde::{Deserialize, Serialize};

// Unified Resource Types
#[derive(Debug, Clone, Serialize, Deserialize)]
pub struct ResourceAllocation {
    pub component: String,
    pub resource_type: ResourceType,
    pub amount: f64,
    pub priority: Priority,
    pub allocated_at: u64,
    pub expires_at: Option<u64>,
}

#[derive(Debug, Clone, Serialize, Deserialize, PartialEq, Eq, Hash)]
pub enum ResourceType {
    CpuCores,
    MemoryBytes,
    NetworkBandwidth,
    StorageBytes,
    CognitiveTokens,
    EconomicBudget,
}

#[derive(Debug, Clone, Serialize, Deserialize, PartialEq, Eq, Hash)]
pub enum Priority {
    Critical,   // System survival
    High,       // Important operations
    Medium,     // Normal operations
    Low,        // Background tasks
}

// Consolidated Economy System (combines body economy + HAL budgeting)
#[derive(Debug)]
pub struct UnifiedResourceManager {
    allocations: Arc<RwLock<HashMap<String, ResourceAllocation>>>,
    resource_pools: Arc<RwLock<ResourcePools>>,
    budget_ledger: Arc<RwLock<BudgetLedger>>,
    policies: Arc<RwLock<ResourcePolicies>>,
}

#[derive(Debug, Default)]
pub struct ResourcePools {
    pub total_cpu_cores: f64,
    pub available_cpu_cores: f64,
    pub total_memory_bytes: u64,
    pub available_memory_bytes: u64,
    pub total_bandwidth: f64, // Mbps
    pub available_bandwidth: f64,
    pub cognitive_tokens: f64,
    pub economic_budget: f64,
}

#[derive(Debug, Default)]
pub struct BudgetLedger {
    pub allocations: HashMap<String, f64>, // component -> budget
    pub expenditures: HashMap<String, f64>, // component -> spent
    pub reputation_weights: HashMap<String, f64>, // component -> reputation multiplier
}

#[derive(Debug, Default)]
pub struct ResourcePolicies {
    pub max_allocation_per_component: HashMap<ResourceType, f64>,
    pub priority_multipliers: HashMap<Priority, f64>,
    pub debt_conservation_enabled: bool,
    pub auto_reclaim_threshold: f64, // percentage
}

impl UnifiedResourceManager {
    pub fn new() -> Self {
        Self {
            allocations: Arc::new(RwLock::new(HashMap::new())),
            resource_pools: Arc::new(RwLock::new(ResourcePools {
                total_cpu_cores: 8.0,
                available_cpu_cores: 8.0,
                total_memory_bytes: 16 * 1024 * 1024 * 1024, // 16GB
                available_memory_bytes: 16 * 1024 * 1024 * 1024,
                total_bandwidth: 1000.0, // 1Gbps
                available_bandwidth: 1000.0,
                cognitive_tokens: 1000.0,
                economic_budget: 10000.0,
            })),
            budget_ledger: Arc::new(RwLock::new(BudgetLedger::default())),
            policies: Arc::new(RwLock::new(ResourcePolicies {
                max_allocation_per_component: [
                    (ResourceType::CpuCores, 4.0),
                    (ResourceType::MemoryBytes, 8.0 * 1024.0 * 1024.0 * 1024.0), // 8GB
                    (ResourceType::NetworkBandwidth, 500.0), // 500Mbps
                    (ResourceType::CognitiveTokens, 500.0),
                    (ResourceType::EconomicBudget, 5000.0),
                ].iter().cloned().collect(),
                priority_multipliers: [
                    (Priority::Critical, 1.0),
                    (Priority::High, 0.8),
                    (Priority::Medium, 0.6),
                    (Priority::Low, 0.3),
                ].iter().cloned().collect(),
                debt_conservation_enabled: true,
                auto_reclaim_threshold: 0.8,
            })),
        }
    }

    // Allocate resources (combines body economy allocation + HAL budgeting)
    pub async fn allocate_resource(&self, request: ResourceRequest) -> Result<ResourceAllocation, AllocationError> {
        let policies = self.policies.read().await;
        let mut pools = self.resource_pools.write().await;
        
        // Check policy limits
        let max_allowed = policies.max_allocation_per_component.get(&request.resource_type)
            .ok_or(AllocationError::UnsupportedResource)?;
        
        if request.amount > *max_allowed {
            return Err(AllocationError::ExceedsPolicyLimit);
        }

        // Apply priority multiplier
        let priority_multiplier = policies.priority_multipliers.get(&request.priority)
            .copied()
            .unwrap_or(1.0);
        
        let adjusted_amount = request.amount * priority_multiplier;

        // Check availability
        let available = self.get_available_amount(&mut pools, &request.resource_type);
        if adjusted_amount > available {
            return Err(AllocationError::InsufficientResources);
        }

        // Allocate resources
        self.consume_resources(&mut pools, &request.resource_type, adjusted_amount);

        let allocation = ResourceAllocation {
            component: request.component.clone(),
            resource_type: request.resource_type.clone(),
            amount: adjusted_amount,
            priority: request.priority.clone(),
            allocated_at: std::time::SystemTime::now()
                .duration_since(std::time::UNIX_EPOCH)
                .unwrap()
                .as_secs(),
            expires_at: request.duration.map(|d| {
                std::time::SystemTime::now()
                    .duration_since(std::time::UNIX_EPOCH)
                    .unwrap()
                    .as_secs() + d
            }),
        };

        // Store allocation
        let allocation_id = format!("alloc_{}", uuid::Uuid::new_v4());
        let mut allocations = self.allocations.write().await;
        allocations.insert(allocation_id.clone(), allocation.clone());

        // Update budget ledger
        let mut ledger = self.budget_ledger.write().await;
        *ledger.allocations.entry(allocation.component.clone())
            .or_insert(0.0) += adjusted_amount;

        println!("Allocated {} {:?} to {} (priority: {:?})", 
                 adjusted_amount, request.resource_type, request.component, request.priority);

        Ok(allocation)
    }

    // Release resources (automatic cleanup)
    pub async fn release_expired_allocations(&self) -> usize {
        let now = std::time::SystemTime::now()
            .duration_since(std::time::UNIX_EPOCH)
            .unwrap()
            .as_secs();

        let mut released_count = 0;
        let mut allocations = self.allocations.write().await;
        let mut pools = self.resource_pools.write().await;

        allocations.retain(|_id, alloc| {
            if let Some(expiry) = alloc.expires_at {
                if now >= expiry {
                    self.return_resources(&mut pools, &alloc.resource_type, alloc.amount);
                    released_count += 1;
                    false // Remove from allocations
                } else {
                    true // Keep allocation
                }
            } else {
                true // Keep indefinite allocations
            }
        });

        released_count
    }

    // Get system metrics (for monitoring)
    pub async fn get_system_metrics(&self) -> SystemMetrics {
        let pools = self.resource_pools.read().await;
        let allocations = self.allocations.read().await;
        let ledger = self.budget_ledger.read().await;

        SystemMetrics {
            cpu_utilization: ((pools.total_cpu_cores - pools.available_cpu_cores) / pools.total_cpu_cores) * 100.0,
            memory_utilization: (((pools.total_memory_bytes - pools.available_memory_bytes) as f64) / (pools.total_memory_bytes as f64)) * 100.0,
            network_utilization: ((pools.total_bandwidth - pools.available_bandwidth) / pools.total_bandwidth) * 100.0,
            active_allocations: allocations.len(),
            total_expenditure: ledger.expenditures.values().sum(),
            available_cognitive_tokens: pools.cognitive_tokens,
            available_budget: pools.economic_budget,
        }
    }

    // Internal helper methods
    fn get_available_amount(&self, pools: &ResourcePools, resource_type: &ResourceType) -> f64 {
        match resource_type {
            ResourceType::CpuCores => pools.available_cpu_cores,
            ResourceType::MemoryBytes => pools.available_memory_bytes as f64,
            ResourceType::NetworkBandwidth => pools.available_bandwidth,
            ResourceType::CognitiveTokens => pools.cognitive_tokens,
            ResourceType::EconomicBudget => pools.economic_budget,
            ResourceType::StorageBytes => 0.0, // Not tracked in this simplified version
        }
    }

    fn consume_resources(&self, pools: &mut ResourcePools, resource_type: &ResourceType, amount: f64) {
        match resource_type {
            ResourceType::CpuCores => pools.available_cpu_cores -= amount,
            ResourceType::MemoryBytes => pools.available_memory_bytes -= amount as u64,
            ResourceType::NetworkBandwidth => pools.available_bandwidth -= amount,
            ResourceType::CognitiveTokens => pools.cognitive_tokens -= amount,
            ResourceType::EconomicBudget => pools.economic_budget -= amount,
            ResourceType::StorageBytes => {} // Not tracked
        }
    }

    fn return_resources(&self, pools: &mut ResourcePools, resource_type: &ResourceType, amount: f64) {
        match resource_type {
            ResourceType::CpuCores => pools.available_cpu_cores += amount,
            ResourceType::MemoryBytes => pools.available_memory_bytes += amount as u64,
            ResourceType::NetworkBandwidth => pools.available_bandwidth += amount,
            ResourceType::CognitiveTokens => pools.cognitive_tokens += amount,
            ResourceType::EconomicBudget => pools.economic_budget += amount,
            ResourceType::StorageBytes => {} // Not tracked
        }
    }
}

// Request and Response Types
#[derive(Debug)]
pub struct ResourceRequest {
    pub component: String,
    pub resource_type: ResourceType,
    pub amount: f64,
    pub priority: Priority,
    pub duration: Option<u64>, // seconds
}

#[derive(Debug)]
pub enum AllocationError {
    InsufficientResources,
    ExceedsPolicyLimit,
    UnsupportedResource,
    InvalidRequest,
}

#[derive(Debug, Serialize)]
pub struct SystemMetrics {
    pub cpu_utilization: f64,
    pub memory_utilization: f64,
    pub network_utilization: f64,
    pub active_allocations: usize,
    pub total_expenditure: f64,
    pub available_cognitive_tokens: f64,
    pub available_budget: f64,
}

// Integration interfaces
impl UnifiedResourceManager {
    // Interface for existing body components
    pub async fn allocate_for_network(&self, component: &str, bandwidth_mbps: f64) -> Result<String, AllocationError> {
        let request = ResourceRequest {
            component: component.to_string(),
            resource_type: ResourceType::NetworkBandwidth,
            amount: bandwidth_mbps,
            priority: Priority::High,
            duration: Some(300), // 5 minutes
        };
        
        self.allocate_resource(request).await
            .map(|_alloc| format!("network_alloc_{}", uuid::Uuid::new_v4()))
    }

    // Interface for HAL cognitive components
    pub async fn allocate_cognitive_budget(&self, component: &str, tokens: f64) -> Result<String, AllocationError> {
        let request = ResourceRequest {
            component: component.to_string(),
            resource_type: ResourceType::CognitiveTokens,
            amount: tokens,
            priority: Priority::Medium,
            duration: Some(60), // 1 minute
        };
        
        self.allocate_resource(request).await
            .map(|_alloc| format!("cog_alloc_{}", uuid::Uuid::new_v4()))
    }
}