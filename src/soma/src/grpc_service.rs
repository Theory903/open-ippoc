use tonic::{transport::Server, Request, Response, Status};
use std::sync::Arc;
use tokio::sync::RwLock;

// Import generated protobuf code
include!(concat!(env!("OUT_DIR"), "/body.rs"));

// Body service implementation
#[derive(Debug, Default)]
pub struct BodyServiceImpl {
    // Shared state between components
    system_state: Arc<RwLock<SystemState>>,
}

#[derive(Debug, Default)]
struct SystemState {
    cpu_usage: f64,
    memory_usage: f64,
    network_throughput: f64,
    active_connections: u32,
}

#[tonic::async_trait]
impl body_service_server::BodyService for BodyServiceImpl {
    
    // Network Operations
    async fn send_packet(
        &self,
        request: Request<PacketRequest>,
    ) -> Result<Response<PacketResponse>, Status> {
        let req = request.into_inner();
        println!("Sending packet to: {}", req.destination_node);
        
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
        
        // Query peer registry
        let response = PeerResponse {
            peer_id: req.peer_id,
            trust_level: "TRUSTED".to_string(),
            last_seen: 1234567890,
            packet_count: 42,
            public_key: vec![0u8; 32], // Placeholder
        };
        
        Ok(Response::new(response))
    }
    
    // Cognitive Operations
    async fn make_decision(
        &self,
        request: Request<DecisionRequest>,
    ) -> Result<Response<DecisionResponse>, Status> {
        let req = request.into_inner();
        println!("Making decision for context: {}", req.context);
        
        // This would integrate with HAL cognition layer
        let response = DecisionResponse {
            selected_option: req.options.first().unwrap_or(&String::new()).clone(),
            confidence: 0.85,
            rationale: "Selected based on current system load and resource availability".to_string(),
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
        
        // Integrate with HAL trust evaluation
        let response = TrustEvaluationResponse {
            should_allow: true,
            trust_level: "PROBATION".to_string(),
            recommendation: "Allow with monitoring".to_string(),
            risk_score: 0.3,
        };
        
        Ok(Response::new(response))
    }
    
    // Resource Management
    async fn allocate_resources(
        &self,
        request: Request<ResourceAllocationRequest>,
    ) -> Result<Response<ResourceAllocationResponse>, Status> {
        let req = request.into_inner();
        
        // Coordinate with economy controller
        let mut state = self.system_state.write().await;
        let allocated = req.amount.min(100.0); // Placeholder limit
        
        let response = ResourceAllocationResponse {
            approved: true,
            allocated_amount: allocated,
            allocation_id: format!("alloc_{}", uuid::Uuid::new_v4()),
            system_load: [
                ("cpu".to_string(), state.cpu_usage),
                ("memory".to_string(), state.memory_usage),
                ("network".to_string(), state.network_throughput),
            ].iter().cloned().collect(),
        };
        
        Ok(Response::new(response))
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
        
        // Integrate with evolution engine
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
        
        // Apply system changes with rollback capability
        let response = ChangeResponse {
            applied: true,
            result: format!("Change {} applied successfully", req.change_id),
            rollback_plan: format!("git revert {}", req.change_id),
        };
        
        Ok(Response::new(response))
    }
}

pub async fn start_grpc_server(port: u16) -> Result<(), Box<dyn std::error::Error>> {
    let addr = format!("0.0.0.0:{}", port).parse()?;
    let body_service = BodyServiceImpl::default();
    
    println!("Starting Body gRPC server on port {}", port);
    
    Server::builder()
        .add_service(body_service_server::BodyServiceServer::new(body_service))
        .serve(addr)
        .await?;
        
    Ok(())
}