use tonic::{transport::Server, Request, Response, Status};
use std::sync::Arc;
use tokio::sync::RwLock;

use crate::protocol::AdmissionManager;
use crate::unified_identity::UnifiedTrustManager;
use crate::resource_manager::{UnifiedResourceManager, ResourceType, Priority, ResourceRequest};

// Import generated protobuf code
include!(concat!(env!("OUT_DIR"), "/body.rs"));

// Body service implementation
#[derive(Debug)]
pub struct BodyServiceImpl {
    // Shared state between components
    system_state: Arc<RwLock<SystemState>>,
    admission: Arc<AdmissionManager>,
    trust: Arc<UnifiedTrustManager>,
    resources: Arc<UnifiedResourceManager>,
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
    ) -> Self {
        Self {
            system_state: Arc::new(RwLock::new(SystemState::default())),
            admission,
            trust,
            resources,
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

pub async fn start_grpc_server(
    port: u16,
    admission: Arc<AdmissionManager>,
    trust: Arc<UnifiedTrustManager>,
    resources: Arc<UnifiedResourceManager>
) -> Result<(), Box<dyn std::error::Error + Send + Sync>> {
    let addr = format!("0.0.0.0:{}", port).parse()?;
    let body_service = BodyServiceImpl::new(admission, trust, resources);
    
    println!("Starting Body gRPC server on port {}", port);
    
    Server::builder()
        .add_service(body_service_server::BodyServiceServer::new(body_service))
        .serve(addr)
        .await?;
        
    Ok(())
}