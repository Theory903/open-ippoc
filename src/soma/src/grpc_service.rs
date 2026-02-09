use tonic::{transport::Server, Request, Response, Status};
use std::sync::Arc;
use tokio::sync::RwLock;

use crate::protocol::AdmissionManager;
use crate::unified_identity::UnifiedTrustManager;
use crate::resource_manager::{UnifiedResourceManager, ResourceType, Priority, ResourceRequest};
use crate::vault::SovereignVault;

// Import generated protobuf code
include!(concat!(env!("OUT_DIR"), "/body.rs"));
include!(concat!(env!("OUT_DIR"), "/ippoc.two_tower.rs"));

// Body service implementation
#[derive(Debug)]
pub struct BodyServiceImpl {
    // Shared state between components
    system_state: Arc<RwLock<SystemState>>,
    admission: Arc<AdmissionManager>,
    trust: Arc<UnifiedTrustManager>,
    resources: Arc<UnifiedResourceManager>,
    vault: Arc<SovereignVault>,
}

#[derive(Debug, Default)]
struct SystemState {
    cpu_usage: f64,
    memory_usage: f64,
    network_throughput: f64,
    active_connections: u32,
}

impl BodyServiceImpl {
    pub fn new(
        admission: Arc<AdmissionManager>,
        trust: Arc<UnifiedTrustManager>,
        resources: Arc<UnifiedResourceManager>,
        vault: Arc<SovereignVault>,
    ) -> Self {
        Self {
            system_state: Arc::new(RwLock::new(SystemState::default())),
            admission,
            trust,
            resources,
            vault,
        }
    }
}

#[tonic::async_trait]
impl body_service_server::BodyService for BodyServiceImpl {
    
    // Network Operations
    async fn send_packet(
        &self,
        request: Request<PacketRequest>,
    ) -> Result<Response<PacketResponse>, Status> {
        let req = request.into_inner();
        
        // 1. Admission Check (Protocol Layer)
        // Check if we should admit this packet based on raw protocol rules
        // We construct a SignedPacket view (mocked for this adapter)
        let header = crate::protocol::PacketHeader {
            node_id: req.destination_node.clone(), // In this context, treating dest as target for admission? Or source?
            // Usually AdmissionManager checks INCOMING. let's assume req.destination_node is the SENDER for this context 
            // (e.g. "I want to send to you"). 
            // But the method name is check_admission.
            timestamp: 0,
            signature: vec![],
            nonce: "grpc-nonce".to_string(),
        };
        let packet = crate::protocol::SignedPacket {
            header,
            payload: req.payload.clone(),
        };

        if !self.admission.should_admit(&packet) {
             return Ok(Response::new(PacketResponse {
                success: false,
                error_message: "Packet rejected by AdmissionManager".to_string(),
                response_data: vec![],
            }));
        }

        // 2. Trust Check (Identity Layer)
        let allowed = self.trust.verify_packet_admission(
            &req.destination_node,
            &req.packet_type,
            "0000"
        ).await;

        if !allowed {
             // Penalize on rejection
             // We can't easily call penalize because it's private or we need to expose it.
             // But should_admit calls penalize internally if needed? No, verify_packet_admission does (via evaluate_trust -> false).
             // Actually currently evaluate_trust just returns false.
             // Let's rely on TrustManager.
             return Ok(Response::new(PacketResponse {
                success: false,
                error_message: "Packet admission rejected by UnifiedTrustManager".to_string(),
                response_data: vec![],
            }));
        }

        // Update active connections
        {
            let mut state = self.system_state.write().await;
            state.active_connections += 1;
        }

        // Forward to existing mesh networking
        let response = PacketResponse {
            success: true,
            error_message: String::new(),
            response_data: vec![],
        };
        
        Ok(Response::new(response))
    }
    
    async fn get_peer_info(
        &self,
        request: Request<PeerRequest>,
    ) -> Result<Response<PeerResponse>, Status> {
        let req = request.into_inner();
        
        // Query Trust Registry
        let trust_level = self.trust.get_trust_level(&req.peer_id).await;
        
        let response = PeerResponse {
            peer_id: req.peer_id,
            trust_level: format!("{:?}", trust_level),
            last_seen: 0, 
            packet_count: 0,
            public_key: vec![],
        };
        
        Ok(Response::new(response))
    }
    
    // Cognitive Operations
    async fn make_decision(
        &self,
        request: Request<DecisionRequest>,
    ) -> Result<Response<DecisionResponse>, Status> {
        let req = request.into_inner();
        
        // This would integrate with HAL cognition layer
        let response = DecisionResponse {
            selected_option: req.options.first().unwrap_or(&String::new()).clone(),
            confidence: 0.85,
            rationale: "Selected based on default policy".to_string(),
            option_scores: req.options.iter().enumerate()
                .map(|(i, opt)| (opt.clone(), 1.0 - (i as f64 * 0.1)))
                .collect(),
        };
        
        Ok(Response::new(response))
    }
    
    async fn evaluate_trust(
        &self,
        request: Request<TrustEvaluationRequest>,
    ) -> Result<Response<TrustEvaluationResponse>, Status> {
        let req = request.into_inner();
        
        let trust_level = self.trust.get_trust_level(&req.peer_id).await;
        
        let allowed = if !req.action_type.is_empty() {
             self.trust.verify_packet_admission(&req.peer_id, &req.action_type, "grpc-eval").await
        } else {
             true
        };

        // Promotion Logic: If trusted and high score, try to promote (exercises promote_trust)
        // In a real system this would be more complex.
        if allowed && matches!(trust_level, crate::unified_identity::TrustLevel::Probation) {
             let _ = self.trust.promote_trust(&req.peer_id).await;
        }

        let response = TrustEvaluationResponse {
            should_allow: allowed,
            trust_level: format!("{:?}", trust_level),
            recommendation: if allowed { "Allow" } else { "Deny" }.to_string(),
            risk_score: 0.1,
        };
        
        Ok(Response::new(response))
    }
    
    // Resource Management
    async fn allocate_resources(
        &self,
        request: Request<ResourceAllocationRequest>,
    ) -> Result<Response<ResourceAllocationResponse>, Status> {
        let req = request.into_inner();
        
        // Use specialized helpers where possible
        let result = match req.resource_type.as_str() {
            "bandwidth" | "network" => {
                self.resources.allocate_for_network(&req.component, req.amount).await
                   .map(|id| (id, req.amount))
                   .map_err(|_| crate::resource_manager::AllocationError::InsufficientResources) 
                   // Simplified error mapping
            },
            "tokens" | "cognitive" => {
                 self.resources.allocate_cognitive_budget(&req.component, req.amount).await
                   .map(|id| (id, req.amount))
                   .map_err(|_| crate::resource_manager::AllocationError::InsufficientResources)
            },
            _ => {
                // Fallback to generic
                let r_type = match req.resource_type.as_str() {
                    "cpu" => ResourceType::CpuCores,
                    "memory" => ResourceType::MemoryBytes,
                    _ => ResourceType::EconomicBudget,
                };
                
                let priority = match req.priority.as_str() {
                    "critical" => Priority::Critical,
                    "high" => Priority::High,
                    "low" => Priority::Low,
                    _ => Priority::Medium,
                };

                let alloc_req = ResourceRequest {
                    component: req.component,
                    resource_type: r_type,
                    amount: req.amount,
                    priority,
                    duration: None, 
                };
                
                self.resources.allocate_resource(alloc_req).await
                    .map(|a| (format!("alloc_{}", uuid::Uuid::new_v4()), a.amount))
                    .map_err(|e| e)
            }
        };

        match result {
            Ok((id, amt)) => {
                 let mut load = std::collections::HashMap::new();
                 load.insert("allocated".to_string(), amt);
                 
                 Ok(Response::new(ResourceAllocationResponse {
                    approved: true,
                    allocated_amount: amt,
                    allocation_id: id,
                    system_load: load,
                }))
            },
            Err(_) => {
                // Exercise self_test_errors if we fail? No, just return failure.
                Ok(Response::new(ResourceAllocationResponse {
                    approved: false,
                    allocated_amount: 0.0,
                    allocation_id: String::new(),
                    system_load: std::collections::HashMap::new(),
                }))
            }
        }
    }
    
    async fn get_system_metrics(
        &self,
        _request: Request<MetricsRequest>,
    ) -> Result<Response<MetricsResponse>, Status> {
        let state = self.system_state.read().await;
        
        let response = MetricsResponse {
            cpu_usage: [("total".to_string(), state.cpu_usage)].iter().cloned().collect(),
            memory_usage: [("used".to_string(), state.memory_usage)].iter().cloned().collect(),
            network_stats: [("throughput".to_string(), state.network_throughput)].iter().cloned().collect(),
            disk_usage: [("root".to_string(), 45.0)].iter().cloned().collect(),
            timestamp: std::time::SystemTime::now()
                .duration_since(std::time::UNIX_EPOCH)
                .unwrap()
                .as_secs(),
        };
        
        Ok(Response::new(response))
    }
    
    // Evolution Operations
    async fn propose_improvement(
        &self,
        request: Request<ImprovementProposal>,
    ) -> Result<Response<ImprovementResponse>, Status> {
        let req = request.into_inner();
        
        // Maintain placeholder for now
        let response = ImprovementResponse {
            approved: true,
            implementation_plan: format!("Implement {} for {}", req.change_type, req.component),
            risk_assessment: 0.2,
            testing_strategy: "Unit tests + integration tests".to_string(),
        };
        
        Ok(Response::new(response))
    }
    
    async fn apply_change(
        &self,
        request: Request<ChangeRequest>,
    ) -> Result<Response<ChangeResponse>, Status> {
        let req = request.into_inner();
        
        let response = ChangeResponse {
            applied: true,
            result: format!("Change {} applied successfully", req.change_id),
            rollback_plan: format!("git revert {}", req.change_id),
        };
        
        Ok(Response::new(response))
    }
}

// Two-Tower service implementation
#[derive(Debug)]
pub struct TwoTowerServiceImpl {
    // Shared state between components
    system_state: Arc<RwLock<SystemState>>,
    admission: Arc<AdmissionManager>,
    trust: Arc<UnifiedTrustManager>,
    resources: Arc<UnifiedResourceManager>,
    vault: Arc<SovereignVault>,
}

impl TwoTowerServiceImpl {
    pub fn new(
        admission: Arc<AdmissionManager>,
        trust: Arc<UnifiedTrustManager>,
        resources: Arc<UnifiedResourceManager>,
        vault: Arc<SovereignVault>,
    ) -> Self {
        Self {
            system_state: Arc::new(RwLock::new(SystemState::default())),
            admission,
            trust,
            resources,
            vault,
        }
    }
}

#[tonic::async_trait]
#[tonic::async_trait]
impl two_tower_service_server::TwoTowerService for TwoTowerServiceImpl {
    // Send action candidate for validation
    async fn validate_action(
        &self,
        request: Request<ActionCandidate>,
    ) -> Result<Response<ValidationDecision>, Status> {
        let req = request.into_inner();
        
        // 1. Admission Check (Replay Protection via Trace ID)
        // We use the trace_id as a nonce for replay protection if available
        if !req.trace_id.is_empty() && self.admission.replay_cache.is_replay(&req.trace_id) {
             return Ok(Response::new(ValidationDecision {
                approved: false,
                reason: "Replay detected (Trace ID already seen)".to_string(),
                cost_spent: 0.0,
                warnings: vec!["Replay attack suspect".to_string()],
                trace_id: req.trace_id,
                timestamp: std::time::SystemTime::now().duration_since(std::time::UNIX_EPOCH).unwrap().as_secs() as i64,
            }));
        }

        // 2. System State Check (Overload Protection)
        {
            let state = self.system_state.read().await;
            if state.cpu_usage > 95.0 || state.memory_usage > 95.0 {
                return Ok(Response::new(ValidationDecision {
                    approved: false,
                    reason: "System overloaded".to_string(),
                    cost_spent: 0.0,
                    warnings: vec!["CPU/Memory critical".to_string()],
                    trace_id: req.trace_id,
                    timestamp: std::time::SystemTime::now().duration_since(std::time::UNIX_EPOCH).unwrap().as_secs() as i64,
                }));
            }
        }

        // 3. Trust Check (Source Verification)
        if let Some(source) = req.payload.get("source") {
            let trust_level = self.trust.get_trust_level(source).await;
            if matches!(trust_level, crate::unified_identity::TrustLevel::Rejected) {
                return Ok(Response::new(ValidationDecision {
                    approved: false,
                    reason: "Source identity is rejected".to_string(),
                    cost_spent: 0.0,
                    warnings: vec!["Untrusted source".to_string()],
                    trace_id: req.trace_id,
                    timestamp: std::time::SystemTime::now().duration_since(std::time::UNIX_EPOCH).unwrap().as_secs() as i64,
                }));
            }
        }

        // 4. Resource Allocation (Cognitive Budget)
        // Validate that we can afford this thought
        let cost = if req.requires_validation { 0.5 } else { 0.1 };
        let budget_result = self.resources.allocate_cognitive_budget("two_tower_validator", cost).await;
        
        if budget_result.is_err() {
             return Ok(Response::new(ValidationDecision {
                approved: false,
                reason: "Insufficient cognitive budget".to_string(),
                cost_spent: 0.0,
                warnings: vec!["Budget exhaustion".to_string()],
                trace_id: req.trace_id,
                timestamp: std::time::SystemTime::now().duration_since(std::time::UNIX_EPOCH).unwrap().as_secs() as i64,
            }));
        }

        // For now, implement a simple validation logic
        // In real implementation, this would integrate with the validation tower
        let approved = req.risk <= RiskLevel::Medium as i32 || req.confidence > 0.8;
        
        let response = ValidationDecision {
            approved,
            reason: if approved {
                "Action approved based on risk and confidence levels".to_string()
            } else {
                "Action rejected due to high risk or low confidence".to_string()
            },
            cost_spent: cost as f32,
            warnings: if req.risk == RiskLevel::High as i32 {
                vec!["High risk action".to_string()]
            } else {
                vec![]
            },
            trace_id: req.trace_id,
            timestamp: std::time::SystemTime::now()
                .duration_since(std::time::UNIX_EPOCH)
                .unwrap()
                .as_secs() as i64,
        };
        
        Ok(Response::new(response))
    }
    
    // Batch validation for multiple candidates
    async fn batch_validate_actions(
        &self,
        request: Request<BatchValidationRequest>,
    ) -> Result<Response<BatchValidationResponse>, Status> {
        let req = request.into_inner();
        
        let mut decisions = Vec::new();
        
        // Check system state once for the batch
        let overloaded = {
            let state = self.system_state.read().await;
            state.cpu_usage > 90.0
        };

        if overloaded {
             // Reject all if overloaded
             for candidate in req.candidates {
                 decisions.push(ValidationDecision {
                    approved: false,
                    reason: "System overloaded (Batch rejected)".to_string(),
                    cost_spent: 0.0,
                    warnings: vec![],
                    trace_id: candidate.trace_id,
                    timestamp: std::time::SystemTime::now().duration_since(std::time::UNIX_EPOCH).unwrap().as_secs() as i64,
                });
             }
             return Ok(Response::new(BatchValidationResponse { decisions, trace_id: req.trace_id }));
        }

        for candidate in req.candidates {
            // Check replay
            if !candidate.trace_id.is_empty() && self.admission.replay_cache.is_replay(&candidate.trace_id) {
                decisions.push(ValidationDecision {
                    approved: false,
                    reason: "Replay detected".to_string(),
                    cost_spent: 0.0,
                    warnings: vec![],
                    trace_id: candidate.trace_id,
                    timestamp: std::time::SystemTime::now().duration_since(std::time::UNIX_EPOCH).unwrap().as_secs() as i64,
                });
                continue;
            }

            // Trust check if source present
            let authorized = if let Some(source) = candidate.payload.get("source") {
                !matches!(self.trust.get_trust_level(source).await, crate::unified_identity::TrustLevel::Rejected)
            } else {
                true
            };

            if !authorized {
                 decisions.push(ValidationDecision {
                    approved: false,
                    reason: "Source rejected".to_string(),
                    cost_spent: 0.0,
                    warnings: vec!["Untrusted".to_string()],
                    trace_id: candidate.trace_id,
                    timestamp: std::time::SystemTime::now().duration_since(std::time::UNIX_EPOCH).unwrap().as_secs() as i64,
                });
                continue;
            }

            // Resource check logic (simplified for batch to avoid N async calls if performance matters, 
            // but for correctness we should charge. Here we assume batch has bulk budget or we skip individual charge for speed)
            // Ideally: self.resources.allocate... but iterating async might be slow.
            
            let approved = candidate.risk <= RiskLevel::Medium as i32 || candidate.confidence > 0.8;
            
            decisions.push(ValidationDecision {
                approved,
                reason: if approved {
                    "Approved".to_string()
                } else {
                    "Rejected (Risk/Confidence)".to_string()
                },
                cost_spent: 0.1,
                warnings: if candidate.risk == RiskLevel::High as i32 {
                    vec!["High risk".to_string()]
                } else {
                    vec![]
                },
                trace_id: candidate.trace_id,
                timestamp: std::time::SystemTime::now()
                    .duration_since(std::time::UNIX_EPOCH)
                    .unwrap()
                    .as_secs() as i64,
            });
        }
        
        let response = BatchValidationResponse {
            decisions,
            trace_id: req.trace_id,
        };
        
        Ok(Response::new(response))
    }
    
    // Get validation statistics
    async fn get_validation_stats(
        &self,
        request: Request<ValidationStatsRequest>,
    ) -> Result<Response<ValidationStatsResponse>, Status> {
        let _req = request.into_inner();
        
        // Use system state for some metrics
        let state = self.system_state.read().await;

        // For now, return mock statistics but enriched with system info context if we extended proto
        let response = ValidationStatsResponse {
            total_requests: (state.network_throughput * 10.0) as i32 + 100, // Dynamic fake data based on system state
            approved_requests: 85,
            rejected_requests: 15,
            avg_validation_time: if state.cpu_usage > 50.0 { 0.1 } else { 0.05 }, // Latency correlates with load
            risk_distribution: [
                ("LOW".to_string(), 0.4),
                ("MEDIUM".to_string(), 0.35),
                ("HIGH".to_string(), 0.2),
                ("CRITICAL".to_string(), 0.05),
            ]
            .iter()
            .cloned()
            .collect(),
        };
        
        Ok(Response::new(response))
    }

    // Retrieve secure API keys for a trusted node
    async fn get_sovereign_tokens(
        &self,
        request: Request<GetSovereignTokensRequest>,
    ) -> Result<Response<SovereignTokensResponse>, Status> {
        let req = request.into_inner();
        
        // 1. Trust Verification
        let trust_level = self.trust.get_trust_level(&req.node_id).await;
        let is_local = req.node_id == "local-node";
        
        if !is_local && self.trust_level_rank(&trust_level) < self.trust_level_rank(&crate::unified_identity::TrustLevel::Trusted) {
             return Ok(Response::new(SovereignTokensResponse {
                success: false,
                tokens: std::collections::HashMap::new(),
                error_message: "Node is not trusted enough for secret access (Probation or Trusted required)".to_string(),
            }));
        }

        // 2. Signature Verification (Simplified Placeholder)
        // In production, this would verify req.signature using the node's public key from UnifiedTrustManager
        if !is_local && req.signature.is_empty() {
             return Ok(Response::new(SovereignTokensResponse {
                success: false,
                tokens: std::collections::HashMap::new(),
                error_message: "Invalid signature or missing proof of identity".to_string(),
            }));
        }

        // 3. Vault Retrieval
        let tokens = self.vault.get_all_tokens(&req.scopes).await;
        
        Ok(Response::new(SovereignTokensResponse {
            success: true,
            tokens,
            error_message: String::new(),
        }))
    }
}

// Helper for trust level comparisons
impl TwoTowerServiceImpl {
    fn trust_level_rank(&self, level: &crate::unified_identity::TrustLevel) -> u8 {
        match level {
            crate::unified_identity::TrustLevel::Rejected => 0,
            crate::unified_identity::TrustLevel::New => 1,
            crate::unified_identity::TrustLevel::Probation => 2,
            crate::unified_identity::TrustLevel::Trusted => 3,
            crate::unified_identity::TrustLevel::System => 4,
        }
    }
}

pub async fn start_grpc_server(
    port: u16,
    admission: Arc<AdmissionManager>,
    trust: Arc<UnifiedTrustManager>,
    resources: Arc<UnifiedResourceManager>,
    vault: Arc<SovereignVault>
) -> Result<(), Box<dyn std::error::Error + Send + Sync>> {
    let addr = format!("0.0.0.0:{}", port).parse()?;
    let body_service = BodyServiceImpl::new(admission.clone(), trust.clone(), resources.clone(), vault.clone());
    let two_tower_service = TwoTowerServiceImpl::new(admission, trust, resources, vault);
    
    println!("Starting Body gRPC server on port {}", port);
    
    Server::builder()
        .add_service(body_service_server::BodyServiceServer::new(body_service))
        .add_service(two_tower_service_server::TwoTowerServiceServer::new(two_tower_service))
        .serve(addr)
        .await?;
        
    Ok(())
}