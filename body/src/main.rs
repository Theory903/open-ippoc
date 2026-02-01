use clap::Parser;
use tracing::{info, warn, error};
use anyhow::Result;
use std::path::{Path, PathBuf}; // Added for Path and PathBuf

mod vllm;
mod sandbox;
mod roles;
mod identity;
mod isolation;
mod protocol;

use vllm::VllmSidecar;
use sandbox::Sandbox;
use roles::RoleManager;
use identity::NodeIdentity;
use isolation::NodeIsolation;
use protocol::AdmissionManager;

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

    // 1. Pre-determine Identity (Phase 4 fix)
    let storage_base = std::env::var("IPPOC_DATA_DIR")
        .map(PathBuf::from)
        .unwrap_or_else(|_| Path::new("/tmp/ippoc").to_path_buf());
    
    let (node_id, signing_key) = NodeIdentity::pre_determine(&storage_base)
        .expect("BOOT FAILURE: Could not determine sovereign identity.");
    let identity = NodeIdentity { node_id: node_id.clone(), signing_key: signing_key.clone() };

    // 2. Initialize Isolation (Phase 2)
    let isolation = NodeIsolation::init(&node_id)
        .expect("BOOT FAILURE: Could not initialize isolation root.");
    info!("Node isolated at {:?}", isolation.root_dir);

    // 3. Persist Identity to Isolation Root
    identity.persist(&isolation.root_dir)
        .expect("BOOT FAILURE: Could not persist sovereign identity to path.");
    info!("Starting IPPOC Node with Sovereign ID: {}", node_id);

    // 4. Initialize Admission Manager (Phase 3)
    let admission = Arc::new(AdmissionManager::new(node_id.clone()));
    
    // Self-pin our own key to allow self-traffic (Rule 2.4 / Identity Uniqueness)
    let my_pub_key = identity.signing_key.verifying_key().to_bytes().to_vec();
    admission.pin_key(node_id.clone(), my_pub_key);

    // 5. Determine Role
    let mut role_manager = RoleManager::new();
    let role = role_manager.determine_role();
    info!("Node initialized as {:?}", role);

    // 4. Initialize Memory (HiDB)
    info!("Initializing HiDB Cognitive Memory within isolation...");
    let database_url = std::env::var("DATABASE_URL").unwrap_or_else(|_| "postgres://ippoc:ippoc@localhost:5432/ippoc".to_string());
    let redis_url = std::env::var("REDIS_URL").unwrap_or_else(|_| "redis://localhost:6379".to_string());
    
    // In Phase 2, HiDB uses the isolated memory path for local state/WAL
    let memory = std::sync::Arc::new(hidb::init(&database_url, &redis_url).await?);

    // 5. Start vLLM Sidecar
    let mut sidecar = VllmSidecar::new(8000);
    // Only start if explicitly requested or auto-detected
    if role == roles::NodeRole::Reasoning {
         if let Err(e) = sidecar.start().await {
             warn!("Sidecar failed to start (is python vllm installed?): {}", e);
         }
    }

    // 5. Initialize Sandbox
    let sandbox = Sandbox::new()?;
    let sandbox_path = isolation.sandbox_path();
    
    // Pre-warm sandbox with a empty module (activates logic)
    if let Err(e) = sandbox.run_wasm(&[], &[], &sandbox_path).await {
         warn!("Sandbox warmup failed (expected if empty): {}", e);
    }
    info!("WASM Sandbox initialized and isolated at {:?}.", sandbox_path);

    if role == roles::NodeRole::Reasoning {
        if sidecar.health_check().await {
            info!("Sidecar is healthy.");
        }
    }

    // 6. Connect to Nervous System (AI Mesh)
    info!("Connecting to P2P Mesh...");
    
    use nervous_system::{AiMesh, MeshConfig};
    let mut config = MeshConfig::default();
    config.port = args.port;
    config.name = node_id.to_string();
    config.role = format!("{:?}", role);

    let (mesh, _outbox, inbox) = AiMesh::new(config);
    mesh.start_networking().await?;
    
    info!("Nervous System: Connected and advertising on port {}.", args.port);

    // 7. Start HTTP API & Reasoning Engine
    info!("Starting Cortex API on 0.0.0.0:{}", args.port);
    
    // Shared State
    use std::sync::Arc;
    use axum::{routing::post, Router, Json};
    use cerebellum::{Cerebrum, ThoughtRequest};
    use brain_evolution::EvolutionEngine;
    use git_evolution::GitEvolution;
    
    // Initialize the Brain
    let brain = Arc::new(Cerebrum::new(memory.clone()));
    let evolution_engine = Arc::new(EvolutionEngine::new(brain.clone()));

    // 8. Auto-Evolution Loop
    let evo_engine = evolution_engine.clone();
    tokio::spawn(async move {
        info!("Auto-Evolution: Monitoring Mind components for mutations...");
        
        let components = [
            ("mind/openclaw", "origin", "main"),
            ("mind/tui", "origin", "main"),
        ];

        loop {
            for (path, remote, branch) in components.iter() {
                // Determine absolute path
                let full_path = std::env::current_dir().unwrap_or_default().join(path);
                
                if !full_path.exists() {
                    warn!("Auto-Evolution: Skip missing component at {:?}", full_path);
                    continue;
                }

                match GitEvolution::open(&full_path) {
                    Ok(evo) => {
                        info!("Auto-Evolution: Checking {} (on {})", path, branch);
                        if let Err(e) = evo.auto_update(remote, branch, evo_engine.as_ref()).await {
                            error!("Auto-Evolution: Mutation failure in {}: {}", path, e);
                        }
                    }
                    Err(e) => {
                        warn!("Auto-Evolution: Could not open git repo at {}: {}", path, e);
                    }
                }
            }
            // Wait 1 hour between cycles
            tokio::time::sleep(tokio::time::Duration::from_secs(3600)).await;
        }
    });

    let app = Router::new()
        .route("/webhook/openclaw", post({
            let brain = brain.clone();
            move |Json(payload): Json<serde_json::Value>| {
                let brain = brain.clone();
                async move {
                    info!("Received signal from OpenClaw: {:?}", payload);
                    
                    // Extract text from OpenClaw payload structure
                    // shape: { event: "agent", payload: { data: { text: "..." } } } or similar
                    let query = payload.get("payload")
                        .and_then(|p| p.get("data"))
                        .and_then(|d| d.get("text"))
                        .and_then(|t| t.as_str())
                        .unwrap_or("");

                    if query.is_empty() {
                         return Json(serde_json::json!({ "status": "ignored", "reason": "no query" }));
                    }

                    // THINK
                    info!("Brain: Thinking about query: '{}'", query);
                    let thought = brain.think(ThoughtRequest {
                        query: query.to_string(),
                        context_history: vec![],
                    }).await;

                    match thought {
                        Ok(resp) => {
                            info!("Brain: Successful reasoning. Answer length: {}", resp.answer.len());
                            Json(serde_json::json!({ 
                                "status": "success", 
                                "thought": {
                                    "answer": resp.answer,
                                    "sources": resp.sources
                                }
                            }))
                        },
                        Err(e) => {
                             error!("Brain: Reasoning failure: {}", e);
                             Json(serde_json::json!({ 
                                 "status": "error", 
                                 "error": e.to_string() 
                             }))
                        }
                    }
                }
            }
        }));

    // Run the HTTP server
    // Note: We run this *alongside* the Mesh if possible, or we let Mesh handle UDP and this handle TCP on same port?
    // possible, or we let Mesh handle UDP and this handle TCP on same port?
    // Usually bad practice to bind same port for different protocols unless SO_REUSEPORT or different sockets.
    // Mesh is likely UDP (QUIC). Axum is TCP. They CAN share the port number technically on some OSs but safer to offset.
    // However, user expects 8080. Let's bind Axum to 8080. Mesh config used 8080 too (UDP). This is fine (UDP vs TCP).
    
    // Process Network Inbox
    let mut inbox_rx = inbox;
    let admission_inbox = admission.clone();
    tokio::spawn(async move {
        while let Ok(msg) = inbox_rx.recv().await {
            // Rule 1.1: Insight Admission Protocol
            info!("Inbound Mesh Message received. Validating signing...");
            
            if let Ok(packet) = serde_json::from_slice::<protocol::SignedPacket>(&msg.payload) {
                if admission_inbox.should_admit(&packet) {
                    info!("Mesh: ADMITTED packet from {}", packet.header.node_id);
                } else {
                    warn!("Mesh: REJECTED packet from {}", packet.header.node_id);
                }
            } else {
                warn!("Mesh: Non-SignedPacket or malformed payload received. Dropping.");
            }
        }
    });

    let addr = std::net::SocketAddr::from(([0, 0, 0, 0], args.port));
    axum::Server::bind(&addr)
        .serve(app.into_make_service())
        .await?;

    Ok(())
}
