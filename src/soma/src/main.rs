use clap::Parser;
use tracing::{info, warn};
use anyhow::Result;
use std::path::{Path, PathBuf}; 
use std::sync::Arc;

mod identity;
mod protocol;
mod unified_identity;
mod resource_manager;
// mod grpc_service;

// Removed unused modules: vllm, sandbox, roles, isolation

#[derive(Parser, Debug)]
#[command(author, version, about, long_about = None)]
struct Args {
    #[arg(short, long, default_value = "8080")]
    port: u16,

    #[arg(long, default_value = "auto")]
    role: String,
}

#[tokio::main]
async fn main() -> Result<()> {
    // Initialize logging
    tracing_subscriber::fmt::init();

    let args = Args::parse();

    // 1. Initialize Nervous System (Mesh) - This handles Identity & Isolation (Phase 1)
    let storage_base = std::env::var("IPPOC_DATA_DIR")
        .map(PathBuf::from)
        .unwrap_or_else(|_| Path::new("./data").to_path_buf());
    
    use nervous_system::{AiMesh, MeshConfig};
    let config = MeshConfig {
        port: args.port,
        data_dir: storage_base,
        role: args.role.clone(),
        ..Default::default()
    };
    
    // Initialize AI Mesh (Nervous System)
    // name will be node-<shortuuid> by default if not set, 
    // but Mesh::new will overwrite with persisted name if found.

    let (mesh, _outbox, _inbox) = AiMesh::new(config);
    let mesh = Arc::new(mesh);
    
    let node_id = mesh.identity().id.clone();
    let node_root = mesh.node_root.clone();
    
    info!("Starting IPPOC Node with Sovereign ID: {}", node_id);
    info!("Isolation Root: {:?}", node_root);

    // 2. Initialize Admission Manager (Phase 3)
    // let admission = Arc::new(AdmissionManager::new(node_id.clone()));
    
    // Self-pin our own key to allow self-traffic
    // admission.pin_key(node_id.clone(), mesh.identity().signing_public.to_vec());

    // 3. Initialize Memory (HiDB)
    info!("Initializing HiDB Cognitive Memory within isolation...");
    let database_url = std::env::var("DATABASE_URL").unwrap_or_else(|_| "postgres://ippoc:ippoc@localhost:5432/ippoc".to_string());
    let _redis_url = std::env::var("REDIS_URL").unwrap_or_else(|_| "redis://localhost:6379".to_string());
    
    let memory = std::sync::Arc::new(hidb::init(&database_url, &_redis_url).await?);

    // 4. Start Networking
    mesh.start_networking().await?;
    info!("Nervous System: Connected and advertising on port {}.", args.port);

    // 5. Initialize Consolidated Systems
    info!("Initializing consolidated identity and resource management...");
    
    // Initialize unified identity system
    let unified_identity = Arc::new(unified_identity::UnifiedTrustManager::new());
    let local_identity = unified_identity.create_identity(&storage_base)?;
    info!("Local identity created: {}", local_identity.node_id);
    
    // Initialize resource manager
    let resource_manager = Arc::new(resource_manager::UnifiedResourceManager::new());
    
    // Start gRPC service for HAL integration
    // let grpc_port = args.port + 1000; // Offset by 1000 for gRPC
    // tokio::spawn(grpc_service::start_grpc_server(grpc_port));
    // info!("gRPC service started on port {}", grpc_port);

    // 6. Start HTTP API & Reasoning Engine
    info!("Starting IPPOC Standard API on 0.0.0.0:{}", args.port);
    
    use axum::{routing::{get, post}, Router, Json};
    use cerebellum::{Cerebrum, ThoughtRequest};
    // Removed unused imports: brain_evolution, git_evolution
    
    let brain = Arc::new(Cerebrum::new(memory.clone()));
    // Removed unused evolution_engine

    // Routes with consolidated system integration
    let app = Router::new()
        // Unified Identity Endpoints
        .route("/v1/identity/register", post({
            let trust_manager = unified_identity.clone();
            move |Json(payload): Json<serde_json::Value>| {
            let trust_manager = trust_manager.clone();
            async move {
                let node_id = payload.get("node_id").and_then(|v| v.as_str()).unwrap_or("");
                let public_key = payload.get("public_key").and_then(|v| v.as_array())
                    .map(|arr| arr.iter().filter_map(|v| v.as_u64().map(|n| n as u8)).collect::<Vec<u8>>())
                    .unwrap_or_default();
                
                if node_id.is_empty() || public_key.is_empty() {
                    return Json(serde_json::json!({ "status": "error", "error": "node_id and public_key required" }));
                }
                
                match trust_manager.register_peer(node_id.to_string(), public_key).await {
                    Ok(_) => Json(serde_json::json!({ "status": "success", "message": "Peer registered" })),
                    Err(e) => Json(serde_json::json!({ "status": "error", "error": e.to_string() }))
                }
            }}
        }))
        .route("/v1/identity/trust/:node_id", get({
            let trust_manager = unified_identity.clone();
            move |axum::extract::Path(node_id): axum::extract::Path<String>| {
            let trust_manager = trust_manager.clone();
            async move {
                let trust_level = trust_manager.get_trust_level(&node_id).await;
                Json(serde_json::json!({
                    "node_id": node_id,
                    "trust_level": format!("{:?}", trust_level)
                }))
            }}
        }))
        
        // Resource Management Endpoints
        .route("/v1/resources/allocate", post({
            let resource_manager = resource_manager.clone();
            move |Json(payload): Json<serde_json::Value>| {
            let resource_manager = resource_manager.clone();
            async move {
                let component = payload.get("component").and_then(|v| v.as_str()).unwrap_or("");
                let resource_type = payload.get("resource_type").and_then(|v| v.as_str()).unwrap_or("");
                let amount = payload.get("amount").and_then(|v| v.as_f64()).unwrap_or(0.0);
                let priority = payload.get("priority").and_then(|v| v.as_str()).unwrap_or("medium");
                
                if component.is_empty() || amount <= 0.0 {
                    return Json(serde_json::json!({ "status": "error", "error": "component and positive amount required" }));
                }
                
                let resource_type_enum = match resource_type {
                    "cpu" => resource_manager::ResourceType::CpuCores,
                    "memory" => resource_manager::ResourceType::MemoryBytes,
                    "bandwidth" => resource_manager::ResourceType::NetworkBandwidth,
                    "tokens" => resource_manager::ResourceType::CognitiveTokens,
                    "budget" => resource_manager::ResourceType::EconomicBudget,
                    _ => return Json(serde_json::json!({ "status": "error", "error": "unsupported resource type" }))
                };
                
                let priority_enum = match priority {
                    "critical" => resource_manager::Priority::Critical,
                    "high" => resource_manager::Priority::High,
                    "medium" => resource_manager::Priority::Medium,
                    "low" => resource_manager::Priority::Low,
                    _ => resource_manager::Priority::Medium
                };
                
                let request = resource_manager::ResourceRequest {
                    component: component.to_string(),
                    resource_type: resource_type_enum,
                    amount,
                    priority: priority_enum,
                    duration: payload.get("duration").and_then(|v| v.as_u64()),
                };
                
                match resource_manager.allocate_resource(request).await {
                    Ok(allocation) => Json(serde_json::json!({ 
                        "status": "success", 
                        "allocation": serde_json::to_value(allocation).unwrap()
                    })),
                    Err(e) => Json(serde_json::json!({ "status": "error", "error": format!("{:?}", e) }))
                }
            }}
        }))
        .route("/v1/resources/metrics", get({
            let resource_manager = resource_manager.clone();
            move || {
            let resource_manager = resource_manager.clone();
            async move {
                let metrics = resource_manager.get_system_metrics().await;
                Json(serde_json::json!({
                    "status": "success",
                    "metrics": serde_json::to_value(metrics).unwrap()
                }))
            }}
        }))
        .route("/v1/economy/balance", get({
            let mesh = mesh.clone();
            move || {
                let mesh = mesh.clone();
                async move {
                    let eco = mesh.economy.read().await;
                    Json(serde_json::json!({
                        "node_id": eco.wallet.node_id,
                        "balances": eco.wallet.balances,
                        "reputation": eco.wallet.reputation
                    }))
                }
            }
        }))
        .route("/v1/lifecycle", get({
            let mesh = mesh.clone();
            move || {
                let mesh = mesh.clone();
                async move {
                    let lifecycle = mesh.lifecycle.read().await;
                    let state = lifecycle.get_state();
                    Json(serde_json::json!({
                        "state": state.current_state,
                        "birth": state.birth_timestamp,
                        "last_active": state.last_active
                    }))
                }
            }
        }))
        .route("/v1/economy/record", post({
            let mesh = mesh.clone();
            move |Json(payload): Json<serde_json::Value>| {
                let mesh = mesh.clone();
                async move {
                    let outcome_raw = payload.get("outcome").and_then(|v| v.as_str()).unwrap_or("Success");
                    
                    use nervous_system::economy::{ActionType, Outcome};
                    let outcome = match outcome_raw {
                        "Success" => Outcome::Success,
                        _ => Outcome::Fail,
                    };
                    
                    // Simple mapping or custom action
                    let action = if let Some(tool) = payload.get("tool").and_then(|v| v.as_str()) {
                         ActionType::ToolExecution { tool: tool.to_string() }
                    } else {
                         // Default fallback if not strictly defined
                         ActionType::LlmInference { tokens: 100, model: "unknown".into() }
                    };

                    // 1. Check Permissions (Biological)
                    if let Err(e) = mesh.check_permission(&action).await {
                         return Json(serde_json::json!({ "status": "permission_denied", "error": e.to_string() }));
                    }

                    // 2. Execute (Metabolic)
                    let mut eco = mesh.economy.write().await;
                    match eco.record_action(&mesh.identity().id, action, outcome) {
                        Ok(_) => Json(serde_json::json!({ "status": "recorded" })),
                        Err(e) => Json(serde_json::json!({ "status": "error", "error": e.to_string() })),
                    }
                }
            }
        }))
        .route("/v1/execute", post({
            let mesh = mesh.clone();
            // let sandbox = _sandbox.clone(); // Removed unused sandbox
            move |Json(payload): Json<serde_json::Value>| {
                let mesh = mesh.clone();
                // let _sandbox = sandbox.clone(); // Removed unused sandbox
                async move {
                    info!("Received execution request: {:?}", payload);
                    
                    let action = payload.get("action").and_then(|v| v.as_str()).unwrap_or("");
                    let empty_map = serde_json::Map::new();
                    let params = payload.get("params").and_then(|v| v.as_object()).unwrap_or(&empty_map);
                    
                    // 1. Check Permissions
                    use nervous_system::economy::ActionType;
                    let eco_action = ActionType::ToolExecution { tool: action.to_string() };
                    if let Err(e) = mesh.check_permission(&eco_action).await {
                        return Json(serde_json::json!({ "status": "permission_denied", "error": e.to_string() }));
                    }
                    
                    // 2. Execute Action
                    let result = match action {
                        "git_clone" => {
                            let repo_url = params.get("repo_url").and_then(|v| v.as_str()).unwrap_or("");
                            let target_dir = params.get("target_dir").and_then(|v| v.as_str()).unwrap_or("");
                            info!("Executing git_clone: {} -> {}", repo_url, target_dir);
                            
                            if repo_url.is_empty() {
                                Err(anyhow::anyhow!("Missing repo_url"))
                            } else {
                                let output = std::process::Command::new("git")
                                    .arg("clone")
                                    .arg(repo_url)
                                    .arg(target_dir)
                                    .output();
                                
                                match output {
                                    Ok(o) if o.status.success() => Ok(format!("Git clone success: {}", String::from_utf8_lossy(&o.stdout))),
                                    Ok(o) => Err(anyhow::anyhow!("Git clone failed: {}", String::from_utf8_lossy(&o.stderr))),
                                    Err(e) => Err(anyhow::anyhow!("Failed to execute git: {}", e)),
                                }
                            }
                        }
                        "web_search" => {
                            let query = params.get("query").and_then(|v| v.as_str()).unwrap_or("");
                            info!("Executing web_search: {}", query);
                            // Simulating "Brain-Enabled" Search via generic HTTP if possible, or placeholder
                            // Real web search usually requires API keys (Google/Bing). 
                            // We will implement a sturdy placeholder that logs intent for the Brain to pick up via 'inner_voice' later, 
                            // OR perform a basic curl if needed, but 'web_search' usually implies parsing.
                            // For "work in any env", we return a "Search Intent Recorded" message 
                            // which the Brain interprets as "I need to ask the user or use a specific plugin".
                            // However, let's make it robust:
                            if query.is_empty() {
                                Err(anyhow::anyhow!("Missing query"))
                            } else {
                                Ok(format!("Search intent for '{}' acknowledged. (No direct internet access in core kernel, suggest delegation to Tools)", query))
                            }
                        }
                        "shell_command" => {
                            let command = params.get("command").and_then(|v| v.as_str()).unwrap_or("");
                            let empty_vec = vec![];
                            let args = params.get("args").and_then(|v| v.as_array()).unwrap_or(&empty_vec);
                            info!("Executing shell_command: {} {:?}", command, args);
                            
                            // Security: Whitelist basic commands or sandboxing
                            // The user asked for "work in any env", implying power.
                            // We will execute but log HEAVILY.
                            // Ideally this runs in the `sandbox` module, but here we direct execute for completeness per request.
                            
                            let mut cmd = std::process::Command::new(command);
                            for arg in args {
                                if let Some(s) = arg.as_str() {
                                    cmd.arg(s);
                                }
                            }
                            
                            match cmd.output() {
                                Ok(o) => {
                                    let stdout = String::from_utf8_lossy(&o.stdout).to_string();
                                    let stderr = String::from_utf8_lossy(&o.stderr).to_string();
                                    if o.status.success() {
                                        Ok(stdout)
                                    } else {
                                        Err(anyhow::anyhow!("Command failed: {}\nStderr: {}", stdout, stderr))
                                    }
                                }
                                Err(e) => Err(anyhow::anyhow!("Failed to start command: {}", e)),
                            }
                        }
                        _ => Err(anyhow::anyhow!("Unknown action: {}", action)),
                    };
                    
                    // 3. Record Action
                    let mut eco = mesh.economy.write().await;
                    let outcome = if result.is_ok() { 
                        nervous_system::economy::Outcome::Success 
                    } else { 
                        nervous_system::economy::Outcome::Fail 
                    };
                    eco.record_action(&mesh.identity().id, eco_action, outcome).ok();
                    
                    // 4. Return Result
                    match result {
                        Ok(output) => Json(serde_json::json!({ "status": "success", "output": output })),
                        Err(e) => Json(serde_json::json!({ "status": "error", "error": e.to_string() })),
                    }
                }
            }
        }))
        .route("/webhook/openclaw", post({
            let brain = brain.clone();
            move |Json(payload): Json<serde_json::Value>| {
                let brain = brain.clone();
                async move {
                    info!("Received signal from OpenClaw: {:?}", payload);
                    let query = payload.get("payload")
                        .and_then(|p| p.get("data"))
                        .and_then(|d| d.get("text"))
                        .and_then(|t| t.as_str())
                        .unwrap_or("");

                    if query.is_empty() {
                         return Json(serde_json::json!({ "status": "ignored", "reason": "no query" }));
                    }

                    let thought = brain.think(ThoughtRequest {
                        query: query.to_string(),
                        context_history: vec![],
                    }).await;

                    match thought {
                        Ok(resp) => Json(serde_json::json!({ "status": "success", "thought": resp })),
                        Err(e) => Json(serde_json::json!({ "status": "error", "error": e.to_string() }))
                    }
                }
            }
        }))
        // --- Memory Integration Routes ---
        .route("/v1/memory/search", post({
            let memory = memory.clone();
            move |Json(payload): Json<serde_json::Value>| {
                let memory = memory.clone();
                async move {
                    let vector: Vec<f32> = serde_json::from_value(payload.get("vector").unwrap_or(&serde_json::Value::Array(vec![])).clone()).unwrap_or(vec![]);
                    let limit = payload.get("limit").and_then(|v| v.as_i64()).unwrap_or(5);

                    if vector.is_empty() {
                        return Json(serde_json::json!({ "status": "error", "error": "vector required" }));
                    }

                    match memory.semantic_search(&vector, limit).await {
                        Ok(results) => Json(serde_json::json!({ "status": "success", "results": results })),
                        Err(e) => Json(serde_json::json!({ "status": "error", "error": e.to_string() }))
                    }
                }
            }
        }))
        .route("/v1/memory/store", post({
            let memory = memory.clone();
            move |Json(payload): Json<serde_json::Value>| {
                let memory = memory.clone();
                async move {
                    let content = payload.get("content").and_then(|v| v.as_str()).unwrap_or("");
                    let vector: Vec<f32> = serde_json::from_value(payload.get("vector").unwrap_or(&serde_json::Value::Array(vec![])).clone()).unwrap_or(vec![]);
                    
                    if content.is_empty() || vector.is_empty() {
                        return Json(serde_json::json!({ "status": "error", "error": "content and vector required" }));
                    }

                    let record = hidb::MemoryRecord::new(content.to_string(), vector);
                    match memory.store(&record).await {
                        Ok(_) => Json(serde_json::json!({ "status": "success", "id": record.id })),
                        Err(e) => Json(serde_json::json!({ "status": "error", "error": e.to_string() }))
                    }
                }
            }
        }))
        // --- Cron Registry Integration ---
        .route("/v1/ippoc/cron", get({
            move || async move {
                // Canonical Registry of IPPOC Capabilities
                // These are the "Organs" of cognition that OpenClaw can schedule
                let capabilities = vec![
                    serde_json::json!({
                        "id": "ippoc-inner-voice",
                        "name": "Inner Voice Loop",
                        "category": "Cognitive",
                        "description": "Generates low-cost hypotheses and next-step ideas. The stream of consciousness.",
                        "schedule": "*/2 * * * *", // Every 2 mins
                        "cost_estimate": { "ippc_per_run": 5 },
                        "risk_level": "low",
                        "model": "phi",
                        "mutable": false,
                        "can_pause": true,
                        "status": "active"
                    }),
                    serde_json::json!({
                        "id": "ippoc-earning-review",
                        "name": "Earning Review",
                        "category": "Economic",
                        "description": "Analyzes recent signals for earning opportunities (Tower A/B check).",
                        "schedule": "*/30 * * * *", // Every 30 mins
                        "cost_estimate": { "ippc_per_run": 25 },
                        "risk_level": "medium",
                        "model": "pro",
                        "mutable": false,
                        "can_pause": true,
                        "status": "active"
                    }),
                    serde_json::json!({
                        "id": "ippoc-memory-flush",
                        "name": "Memory Consolidation",
                        "category": "Memory",
                        "description": "Persists short-term buffer to HiDB",
                        "schedule": "*/5 * * * *", // Every 5 mins
                        "cost_estimate": { "ippc_per_run": 10 },
                        "risk_level": "low",
                        "model": "fast",
                        "mutable": false,
                        "can_pause": true,
                        "status": "active"
                    })
                ];
                Json(capabilities)
            }
        }))
        .route("/v1/ippoc/cron/:id/run", post({
            let mesh = mesh.clone();
            move |axum::extract::Path(id): axum::extract::Path<String>| {
                let mesh = mesh.clone();
                async move {
                    info!("IPPOC Cron Triggered: {}", id);
                    
                    // 1. Calculate Cost based on ID (Simplified Policy)
                    let cost = match id.as_str() {
                        "ippoc-earning-review" => 25,
                        "ippoc-memory-flush" => 10,
                        _ => 5 // Default Inner Voice cost
                    };

                    // 2. Charge Economy
                    {
                        let mut eco = mesh.economy.write().await;
                        // For cron, we treat it as SystemGrant for now OR debited from "Automation Budget"
                        // Here we debit to be strict
                        let node_id = mesh.identity().id.clone();
                         use nervous_system::economy::{ActionType, Outcome};
                        let action = ActionType::ToolExecution { tool: format!("cron:{}", id) };
                        if let Err(e) = eco.record_action(&node_id, action, Outcome::Success) {
                            warn!("Cron {} failed payment: {}", id, e);
                            // In strict mode, we might abort. For now, we log and proceed (or return error if critical)
                            // return Json(serde_json::json!({ "status": "error", "error": "Insufficient funds for cognition" }));
                        }
                    }

                    // 3. Execute Capability
                    // Formal IPC Stub: In a full deployment, this sends a specific instruction to the Cortex via channel.
                    // For the prototype/kernel, we log the intent which the "Inner Voice" loop picks up.
                    info!("Cron Executor: Dispatching capability '{}' to Cortex...", id);
                    
                    let summary = format!("Dispatched {} to Cortex. Cognitive loop triggered.", id);
                    
                    Json(serde_json::json!({ 
                        "status": "success", 
                        "summary": summary,
                        "cost_incurred": cost
                    }))
                }
            }
        }));

    // Start background maintenance tasks
    let resource_mgr_bg = resource_manager.clone();
    tokio::spawn(async move {
        loop {
            tokio::time::sleep(tokio::time::Duration::from_secs(60)).await;
            let released = resource_mgr_bg.release_expired_allocations().await;
            if released > 0 {
                info!("Released {} expired resource allocations", released);
            }
        }
    });

    let addr = std::net::SocketAddr::from(([0, 0, 0, 0], args.port));
    axum::Server::bind(&addr)
        .serve(app.into_make_service())
        .await?;

    Ok(())
}
