use btleplug::api::{Central, Manager as _, Peripheral as _, ScanFilter, WriteType};
use btleplug::platform::{Manager, Peripheral};
use tokio::sync::mpsc;
use tokio::time::{self, Duration};
use futures::stream::StreamExt;
use std::collections::{HashMap, HashSet};
use std::sync::Arc;
use tokio::sync::Mutex;
use axum::{Router, routing::post, Json};
use std::net::SocketAddr;
use bloomfilter::Bloom;
use rand::Rng;
use anyhow::{Context, Result};
use tracing::{debug, error, info, warn};

mod tui;
use tui::app::{App, TuiPhase};
use tui::tui as tui_mod;
use tui::ui;
use tui::event;
use crossterm::event as crossterm_event;
use crossterm::event::Event as CrosstermEvent;
use std::time::Duration as StdDuration;

// Module declarations
mod compression;
mod fragmentation;
mod encryption;
mod terminal_ux;
mod persistence;
mod data_structures;
mod payload_handling;
mod packet_parser;
mod packet_creation;
mod packet_delivery;
mod command_handling;
mod message_handlers;
mod notification_handlers;
mod binary_protocol_utils;
mod binary_encoding;
mod noise_protocol;
mod noise_session;

use encryption::EncryptionService;
use terminal_ux::{ChatContext, ChatMode};
use persistence::{AppState, load_state, save_state};
use packet_parser::{parse_bitchat_packet, generate_keys_and_payload};
use packet_creation::create_bitchat_packet;
use command_handling::*;
use message_handlers::{handle_private_dm_message, handle_regular_message};
use notification_handlers::*;
use crate::data_structures::{
    DebugLevel, DEBUG_LEVEL, MessageType, Peer,
    DeliveryTracker, FragmentCollector, BITCHAT_SERVICE_UUID, BITCHAT_CHARACTERISTIC_UUID,
};
use crate::noise_session::NoiseSessionManager;
use x25519_dalek::StaticSecret;

// ============================================================================
// Constants
// ============================================================================

const BT_SCAN_TIMEOUT_SECS: u64 = 15;
const BT_CONNECTION_RETRY_DELAY_MS: u64 = 500;
const TICK_RATE_MS: u64 = 100;
const NOTIFICATION_TIMEOUT_MS: u64 = 1;
const BLOOM_FILTER_CAPACITY: usize = 500;
const BLOOM_FILTER_FP_RATE: f64 = 0.01;
const TELEPATHY_BRIDGE_PORT: u16 = 8003;
const UI_CHANNEL_BUFFER: usize = 100;
const INPUT_CHANNEL_BUFFER: usize = 10;
const TELEPATHY_CHANNEL_BUFFER: usize = 100;

// ============================================================================
// Error Types
// ============================================================================

#[derive(Debug, thiserror::Error)]
pub enum BitchatError {
    #[error("Bluetooth adapter not found")]
    NoBluetoothAdapter,
    
    #[error("BitChat service not found within timeout")]
    ServiceNotFound,
    
    #[error("Connection failed: {0}")]
    ConnectionFailed(String),
    
    #[error("Bluetooth error: {0}")]
    BluetoothError(#[from] btleplug::Error),
    
    #[error("Channel send error: {0}")]
    ChannelSendError(String),
    
    #[error("State persistence error: {0}")]
    StatePersistenceError(String),
}

// ============================================================================
// Application State Container
// ============================================================================

/// Central state container for the BitChat application
pub struct BitchatState {
    // Identity
    pub my_peer_id: String,
    pub nickname: String,
    
    // Networking
    pub peers: Arc<Mutex<HashMap<String, Peer>>>,
    pub blocked_peers: HashSet<String>,
    
    // Messaging
    pub chat_context: ChatContext,
    pub delivery_tracker: DeliveryTracker,
    pub fragment_collector: FragmentCollector,
    
    // Encryption & Security
    pub encryption_service: Arc<EncryptionService>,
    pub noise_session_manager: NoiseSessionManager,
    
    // Channels
    pub channel_keys: HashMap<String, [u8; 32]>,
    pub channel_creators: HashMap<String, String>,
    pub password_protected_channels: HashSet<String>,
    pub channel_key_commitments: HashMap<String, String>,
    pub discovered_channels: HashSet<String>,
    
    // Deduplication
    pub bloom: Bloom<String>,
    
    // Persistence
    pub app_state: AppState,
}

impl BitchatState {
    /// Initialize a new BitchatState from saved or default values
    pub fn new() -> Result<Self> {
        let saved_state = load_state();
        
        // Generate peer ID
        let mut peer_id_bytes = [0u8; 4];
        rand::thread_rng().fill(&mut peer_id_bytes);
        let my_peer_id = hex::encode(&peer_id_bytes);
        
        // Get or create nickname
        let nickname = saved_state.nickname
            .clone()
            .unwrap_or_else(|| "anonymous".to_string());
        
        // Initialize encryption
        let encryption_service = Arc::new(EncryptionService::new());
        
        // Initialize Noise protocol
        let static_secret = if let Some(noise_key_bytes) = &saved_state.noise_static_key {
            let key_array: [u8; 32] = noise_key_bytes
                .as_slice()
                .try_into()
                .unwrap_or([0u8; 32]);
            StaticSecret::from(key_array)
        } else {
            StaticSecret::random_from_rng(&mut rand::thread_rng())
        };
        
        let noise_session_manager = NoiseSessionManager::new(static_secret);
        
        Ok(Self {
            my_peer_id,
            nickname,
            peers: Arc::new(Mutex::new(HashMap::new())),
            blocked_peers: saved_state.blocked_peers.clone(),
            chat_context: ChatContext::new(),
            delivery_tracker: DeliveryTracker::new(),
            fragment_collector: FragmentCollector::new(),
            encryption_service,
            noise_session_manager,
            channel_keys: HashMap::new(),
            channel_creators: saved_state.channel_creators.clone(),
            password_protected_channels: saved_state.password_protected_channels.clone(),
            channel_key_commitments: saved_state.channel_key_commitments.clone(),
            discovered_channels: HashSet::new(),
            bloom: Bloom::<String>::new_for_fp_rate(BLOOM_FILTER_CAPACITY, BLOOM_FILTER_FP_RATE),
            app_state: saved_state,
        })
    }
    
    /// Save the current state to persistent storage
    pub fn save(&self) -> Result<()> {
        let state = AppState {
            nickname: Some(self.nickname.clone()),
            blocked_peers: self.blocked_peers.clone(),
            channel_creators: self.channel_creators.clone(),
            joined_channels: self.chat_context.active_channels.iter().cloned().collect(),
            password_protected_channels: self.password_protected_channels.clone(),
            channel_key_commitments: self.channel_key_commitments.clone(),
            favorites: self.app_state.favorites.clone(),
            identity_key: self.app_state.identity_key.clone(),
            noise_static_key: self.app_state.noise_static_key.clone(),
            encrypted_channel_passwords: self.app_state.encrypted_channel_passwords.clone(),
        };
        
        save_state(&state).map_err(|e| {
            anyhow::anyhow!("Failed to save state: {}", e)
        })
    }
}

// ============================================================================
// Bluetooth Connection Management
// ============================================================================

/// Handles Bluetooth connection setup with proper error handling
async fn setup_bluetooth_connection(
    ui_tx: mpsc::Sender<String>,
) -> Result<Peripheral, BitchatError> {
    // Initialize Bluetooth manager
    let manager = Manager::new()
        .await
        .map_err(BitchatError::BluetoothError)?;
    
    let adapters = manager.adapters()
        .await
        .map_err(BitchatError::BluetoothError)?;
    
    let adapter = adapters
        .into_iter()
        .next()
        .ok_or(BitchatError::NoBluetoothAdapter)?;
    
    // Start scanning
    adapter.start_scan(ScanFilter::default())
        .await
        .map_err(BitchatError::BluetoothError)?;
    
    send_ui_message(&ui_tx, "\x1b[90m» Scanning for bitchat service...\x1b[0m").await?;
    
    debug!("Starting Bluetooth scan for BitChat service");
    
    let start_time = std::time::Instant::now();
    let timeout_duration = Duration::from_secs(BT_SCAN_TIMEOUT_SECS);
    
    // Scan loop with timeout
    let peripheral = loop {
        if let Some(p) = find_peripheral(&adapter).await? {
            send_ui_message(&ui_tx, "\x1b[90m» Found bitchat service! Connecting...\x1b[0m").await?;
            info!("BitChat service found, attempting connection");
            adapter.stop_scan().await?;
            break p;
        }
        
        if start_time.elapsed() >= timeout_duration {
            adapter.stop_scan().await?;
            let error_message = format_bluetooth_timeout_error();
            send_ui_message(&ui_tx, &error_message).await?;
            return Err(BitchatError::ServiceNotFound);
        }
        
        time::sleep(Duration::from_secs(1)).await;
    };
    
    // Attempt connection
    if let Err(e) = peripheral.connect().await {
        let error_message = format_bluetooth_connection_error(&e);
        send_ui_message(&ui_tx, &error_message).await?;
        return Err(BitchatError::ConnectionFailed(e.to_string()));
    }
    
    info!("Successfully connected to BitChat service");
    Ok(peripheral)
}

/// Find a peripheral advertising the BitChat service
async fn find_peripheral(
    adapter: &btleplug::platform::Adapter,
) -> Result<Option<Peripheral>, btleplug::Error> {
    for p in adapter.peripherals().await? {
        if let Ok(Some(properties)) = p.properties().await {
            if properties.services.contains(&BITCHAT_SERVICE_UUID) {
                return Ok(Some(p));
            }
        }
    }
    Ok(None)
}

// ============================================================================
// Bluetooth Connection Initialization
// ============================================================================

/// Initialize Bluetooth connection after successful connection
async fn initialize_bluetooth_connection(
    peripheral: &Peripheral,
    state: &mut BitchatState,
) -> Result<(
    futures::stream::BoxStream<'static, btleplug::api::ValueNotification>,
    btleplug::api::Characteristic,
)> {
    // Discover services
    peripheral.discover_services()
        .await
        .context("Failed to discover services")?;
    
    let chars = peripheral.characteristics();
    let cmd_char = chars
        .iter()
        .find(|c| c.uuid == BITCHAT_CHARACTERISTIC_UUID)
        .ok_or_else(|| anyhow::anyhow!("BitChat characteristic not found"))?
        .clone();
    
    // Subscribe to notifications
    peripheral.subscribe(&cmd_char)
        .await
        .context("Failed to subscribe to characteristic")?;
    
    let notification_stream = peripheral.notifications()
        .await
        .context("Failed to get notification stream")?;
    
    // Perform initial handshake
    perform_initial_handshake(peripheral, &cmd_char, state).await?;
    
    Ok((notification_stream, cmd_char))
}

/// Perform the initial key exchange and announce handshake
async fn perform_initial_handshake(
    peripheral: &Peripheral,
    cmd_char: &btleplug::api::Characteristic,
    state: &BitchatState,
) -> Result<()> {
    // Send key exchange
    let (kxp, _) = generate_keys_and_payload(&state.encryption_service);
    let kx_packet = create_bitchat_packet(
        &state.my_peer_id,
        MessageType::KeyExchange,
        kxp,
    );
    
    peripheral.write(cmd_char, &kx_packet, WriteType::WithoutResponse)
        .await
        .context("Failed to send key exchange")?;
    
    time::sleep(Duration::from_millis(BT_CONNECTION_RETRY_DELAY_MS)).await;
    
    // Send announce
    let announce_packet = create_bitchat_packet(
        &state.my_peer_id,
        MessageType::Announce,
        state.nickname.as_bytes().to_vec(),
    );
    
    peripheral.write(cmd_char, &announce_packet, WriteType::WithoutResponse)
        .await
        .context("Failed to send announce")?;
    
    info!("Initial handshake completed for peer {}", state.my_peer_id);
    Ok(())
}

// ============================================================================
// Notification Processing
// ============================================================================

/// Process incoming Bluetooth notifications
async fn process_notification(
    notification: btleplug::api::ValueNotification,
    state: &mut BitchatState,
    peripheral: &Peripheral,
    cmd_char: &btleplug::api::Characteristic,
    ui_tx: &mpsc::Sender<String>,
    app: &mut App,
) -> Result<()> {
    debug!("Processing notification: {} bytes", notification.value.len());
    
    let packet = parse_bitchat_packet(&notification.value)
        .map_err(|e| anyhow::anyhow!(e))
        .context("Failed to parse BitChat packet")?;
    
    // Ignore our own packets
    if packet.sender_id_str == state.my_peer_id {
        return Ok(());
    }
    
    debug!(
        "Received packet: type={:?}, sender={}, recipient={:?}",
        packet.msg_type,
        packet.sender_id_str,
        packet.recipient_id_str
    );
    
    let mut peers_lock = state.peers.lock().await;
    
    // Dispatch to appropriate handler
    match packet.msg_type {
        MessageType::Announce => {
            handle_announce_message(&packet, &mut peers_lock, ui_tx.clone()).await;
        }
        MessageType::Message => {
            handle_message_packet(
                &packet,
                &notification.value,
                &mut peers_lock,
                &mut state.bloom,
                &mut state.discovered_channels,
                &mut state.password_protected_channels,
                &mut state.channel_keys,
                &mut state.chat_context,
                &mut state.delivery_tracker,
                &state.encryption_service,
                &mut state.noise_session_manager,
                peripheral,
                cmd_char,
                &state.nickname,
                &state.my_peer_id,
                &state.blocked_peers,
                ui_tx.clone(),
            ).await;
        }
        MessageType::FragmentStart | MessageType::FragmentContinue | MessageType::FragmentEnd => {
            handle_fragment_packet(
                &packet,
                &notification.value,
                &mut state.fragment_collector,
                &mut peers_lock,
                &mut state.bloom,
                &mut state.discovered_channels,
                &mut state.password_protected_channels,
                &mut state.chat_context,
                &state.encryption_service,
                peripheral,
                cmd_char,
                &state.nickname,
                &state.my_peer_id,
                &state.blocked_peers,
                ui_tx.clone(),
            ).await;
        }
        MessageType::KeyExchange => {
            handle_key_exchange_message(
                &packet,
                &mut peers_lock,
                &state.encryption_service,
                peripheral,
                cmd_char,
                &state.my_peer_id,
                ui_tx.clone(),
            ).await;
        }
        MessageType::Leave => {
            handle_leave_message(
                &packet,
                &mut peers_lock,
                &state.chat_context,
                ui_tx.clone(),
            ).await;
        }
        MessageType::ChannelAnnounce => {
            let payload_str = String::from_utf8_lossy(&packet.payload);
            let parts: Vec<&str> = payload_str.split('|').collect();
            if parts.len() >= 3 {
                let channel_name = parts[0].to_string();
                if channel_name != "#public" && !app.channels.contains(&channel_name) {
                    app.channels.push(channel_name.clone());
                }
            }
            
            handle_channel_announce_message(
                &packet,
                &mut state.channel_creators,
                &mut state.password_protected_channels,
                &mut state.channel_keys,
                &mut state.channel_key_commitments,
                &mut state.chat_context,
                &state.blocked_peers,
                &state.app_state.encrypted_channel_passwords,
                &state.nickname,
                &|blocked, creators, channels, protected, commitments, encrypted_passwords, nickname| {
                    AppState {
                        nickname: Some(nickname.to_string()),
                        blocked_peers: blocked.clone(),
                        channel_creators: creators.clone(),
                        joined_channels: channels.to_vec(),
                        password_protected_channels: protected.clone(),
                        channel_key_commitments: commitments.clone(),
                        favorites: state.app_state.favorites.clone(),
                        identity_key: state.app_state.identity_key.clone(),
                        noise_static_key: state.app_state.noise_static_key.clone(),
                        encrypted_channel_passwords: encrypted_passwords.clone(),
                    }
                },
                ui_tx.clone(),
            ).await;
        }
        MessageType::DeliveryAck => {
            handle_delivery_ack_message(
                &packet,
                &notification.value,
                &state.encryption_service,
                &mut state.delivery_tracker,
                peripheral,
                cmd_char,
                &state.my_peer_id,
                ui_tx.clone(),
            ).await;
        }
        MessageType::DeliveryStatusRequest => {
            handle_delivery_status_request_message(&packet, ui_tx.clone()).await;
        }
        MessageType::ReadReceipt => {
            handle_read_receipt_message(&packet, ui_tx.clone()).await;
        }
        MessageType::NoiseHandshakeInit => {
            handle_noise_handshake_init(
                &packet,
                &mut state.noise_session_manager,
                peripheral,
                cmd_char,
                &state.my_peer_id,
                ui_tx.clone(),
            ).await;
        }
        MessageType::NoiseHandshakeResp => {
            handle_noise_handshake_resp(
                &packet,
                &mut state.noise_session_manager,
                peripheral,
                cmd_char,
                &state.my_peer_id,
                ui_tx.clone(),
            ).await;
        }
        MessageType::Telepathy => {
            handle_telepathy_packet(&packet, &mut peers_lock, ui_tx.clone()).await;
        }
        MessageType::NoiseEncrypted => {
            handle_noise_encrypted_message(
                &packet,
                &mut state.noise_session_manager,
                &mut peers_lock,
                &mut state.bloom,
                &mut state.discovered_channels,
                &mut state.password_protected_channels,
                &mut state.channel_keys,
                &mut state.chat_context,
                &mut state.delivery_tracker,
                &state.encryption_service,
                peripheral,
                cmd_char,
                &state.nickname,
                &state.my_peer_id,
                &state.blocked_peers,
                ui_tx.clone(),
            ).await;
        }
        MessageType::NoiseIdentityAnnounce => {
            handle_noise_identity_announce(
                &packet,
                &mut peers_lock,
                &mut state.noise_session_manager,
                ui_tx.clone(),
            ).await;
        }
        MessageType::HandshakeRequest => {
            handle_handshake_request_message(
                &packet,
                &mut state.noise_session_manager,
                peripheral,
                cmd_char,
                &state.my_peer_id,
                ui_tx.clone(),
            ).await;
        }
        _ => {
            debug!("Ignoring unknown packet type: {:?}", packet.msg_type);
        }
    }
    
    Ok(())
}

// ============================================================================
// Telepathy Bridge Server
// ============================================================================

/// Start the Telepathy bridge server for receiving messages from Brain
fn start_telepathy_bridge(
    telepathy_tx: mpsc::Sender<serde_json::Value>,
) -> tokio::task::JoinHandle<()> {
    tokio::spawn(async move {
        let app = Router::new()
            .route("/telepathy", post(move |Json(payload): Json<serde_json::Value>| {
                let tx = telepathy_tx.clone();
                async move {
                    debug!("Received telepathy from brain: {}", payload);
                    let _ = tx.send(payload).await;
                    axum::http::StatusCode::OK
                }
            }));
        
        let addr = SocketAddr::from(([127, 0, 0, 1], TELEPATHY_BRIDGE_PORT));
        match tokio::net::TcpListener::bind(addr).await {
            Ok(listener) => {
                info!("Telepathy bridge server started on {}", addr);
                let _ = axum::serve(listener, app).await;
            }
            Err(e) => {
                error!("Failed to start telepathy bridge server: {}", e);
            }
        }
    })
}

// ============================================================================
// Main Application Loop
// ============================================================================

#[tokio::main]
async fn main() -> Result<()> {
    // Initialize logging
    tracing_subscriber::fmt::init();
    
    info!("Starting BitChat application");
    
    // Create communication channels
    let (input_tx, mut input_rx) = mpsc::channel::<String>(INPUT_CHANNEL_BUFFER);
    let (telepathy_tx, mut telepathy_rx) = mpsc::channel::<serde_json::Value>(TELEPATHY_CHANNEL_BUFFER);
    let (ui_tx, mut ui_rx) = mpsc::channel::<String>(UI_CHANNEL_BUFFER);
    
    // Start Telepathy Bridge Server
    let _telepathy_handle = start_telepathy_bridge(telepathy_tx);
    
    // Initialize application state
    let mut state = BitchatState::new()
        .context("Failed to initialize application state")?;
    
    // Initialize TUI
    let mut terminal = tui_mod::init()
        .context("Failed to initialize TUI")?;
    let mut app = App::new_with_nickname(state.nickname.clone());
    
    // Spawn Bluetooth connection setup
    let ui_tx_clone = ui_tx.clone();
    let mut bt_handle = Some(tokio::spawn(async move {
        match setup_bluetooth_connection(ui_tx_clone.clone()).await {
            Ok(peripheral) => {
                let _ = ui_tx_clone.send("__CONNECTED__".to_string()).await;
                Ok(peripheral)
            }
            Err(e) => {
                let _ = ui_tx_clone.send(format!("__ERROR__{}", e)).await;
                Err(e)
            }
        }
    }));
    
    // Bluetooth connection state
    let mut peripheral: Option<Peripheral> = None;
    let mut notification_stream: Option<
        futures::stream::BoxStream<'static, btleplug::api::ValueNotification>,
    > = None;
    let mut cmd_char = None;
    let mut post_connect_initialized = false;
    
    // Main event loop
    let mut last_tick = std::time::Instant::now();
    let tick_rate = StdDuration::from_millis(TICK_RATE_MS);
    
    'mainloop: loop {
        // Handle UI messages
        while let Ok(msg) = ui_rx.try_recv() {
            handle_ui_message(&msg, &mut app, &mut peripheral, &mut bt_handle).await;
        }
        
        // Initialize Bluetooth connection after successful connection
        if !post_connect_initialized && matches!(app.phase, TuiPhase::Connected) {
            if let Some(ref p) = peripheral {
                match initialize_bluetooth_connection(p, &mut state).await {
                    Ok((stream, char)) => {
                        notification_stream = Some(stream);
                        cmd_char = Some(char);
                        post_connect_initialized = true;
                        info!("Bluetooth connection initialized successfully");
                    }
                    Err(e) => {
                        error!("Failed to initialize Bluetooth connection: {}", e);
                        app.add_log_message(format!("system: Connection initialization failed: {}", e));
                    }
                }
            }
        }
        
        // Process Bluetooth notifications
        if let (Some(notification_stream), true) = (notification_stream.as_mut(), post_connect_initialized) {
            if let Ok(Some(notification)) = tokio::time::timeout(
                std::time::Duration::from_millis(NOTIFICATION_TIMEOUT_MS),
                notification_stream.next()
            ).await {
                if let Err(e) = process_notification(
                    notification,
                    &mut state,
                    peripheral.as_ref().unwrap(),
                    cmd_char.as_ref().unwrap(),
                    &ui_tx,
                    &mut app,
                ).await {
                    error!("Error processing notification: {}", e);
                }
            }
        }
        
        // Handle keyboard input events
        if crossterm_event::poll(tick_rate.saturating_sub(last_tick.elapsed())).unwrap_or(false) {
            if let CrosstermEvent::Key(key_event) = crossterm_event::read().unwrap() {
                event::handle_key_event(&mut app, key_event, &input_tx);
            }
        }
        
        // Handle pending UI state changes
        handle_pending_state_changes(&mut app, &mut state, peripheral.as_ref(), cmd_char.as_ref()).await;
        
        // Handle user input from input box
        while let Ok(line) = input_rx.try_recv() {
            if let Err(e) = handle_user_input(
                &line,
                &mut state,
                &mut app,
                peripheral.as_ref(),
                cmd_char.as_ref(),
                &ui_tx,
            ).await {
                error!("Error handling user input: {}", e);
                app.add_log_message(format!("system: Error: {}", e));
            }
        }
        
        // Handle telepathy messages
        while let Ok(msg) = telepathy_rx.try_recv() {
            handle_telepathy_message(msg, &state, peripheral.as_ref(), cmd_char.as_ref(), &ui_tx).await;
        }
        
        // Render UI
        terminal.draw(|f| ui::render(&mut app, f))
            .context("Failed to render UI")?;
        
        // Check for exit
        if app.should_quit {
            break 'mainloop;
        }
        
        last_tick = std::time::Instant::now();
    }
    
    // Cleanup
    info!("Shutting down BitChat application");
    tui_mod::restore().context("Failed to restore terminal")?;
    
    Ok(())
}

// ============================================================================
// Helper Functions
// ============================================================================

async fn send_ui_message(tx: &mpsc::Sender<String>, msg: &str) -> Result<(), BitchatError> {
    tx.send(msg.to_string())
        .await
        .map_err(|e| BitchatError::ChannelSendError(e.to_string()))
}

fn format_bluetooth_timeout_error() -> String {
    [
        "\n\x1b[91m❌ No BitChat service found\x1b[0m",
        "\x1b[90mScan timed out after 15 seconds.\x1b[0m",
        "\x1b[90mPlease check:\x1b[0m",
        "\x1b[90m  • Another device is running BitChat\x1b[0m",
        "\x1b[90m  • Bluetooth is enabled on both devices\x1b[0m",
        "\x1b[90m  • You're within Bluetooth range\x1b[0m",
        "\x1b[90m  • The other device is advertising the BitChat service\x1b[0m",
    ].join("\n")
}

fn format_bluetooth_connection_error(error: &btleplug::Error) -> String {
    format!(
        "\n\x1b[91m❌ Connection failed\x1b[0m\n\
        \x1b[90mReason: {}\x1b[0m\n\
        \x1b[90mPlease check:\x1b[0m\n\
        \x1b[90m  • Bluetooth is enabled\x1b[0m\n\
        \x1b[90m  • The other device is running BitChat\x1b[0m\n\
        \x1b[90m  • You're within range\x1b[0m\n\n\
        \x1b[90mTry running the command again.\x1b[0m\n",
        error
    )
}

async fn handle_ui_message(
    msg: &str,
    app: &mut App,
    peripheral: &mut Option<Peripheral>,
    bt_handle: &mut Option<tokio::task::JoinHandle<Result<Peripheral, BitchatError>>>,
) {
    if msg == "__CONNECTED__" {
        app.transition_to_connected();
        if peripheral.is_none() {
            if let Some(handle) = bt_handle.take() {
                if let Ok(Ok(periph)) = handle.await {
                    *peripheral = Some(periph);
                }
            }
        }
    } else if let Some(err) = msg.strip_prefix("__ERROR__") {
        app.transition_to_error(err.to_string());
    } else if matches!(app.phase, TuiPhase::Connecting) {
        app.add_popup_message(msg.to_string());
    } else {
        app.add_log_message(msg.to_string());
    }
}

async fn handle_pending_state_changes(
    app: &mut App,
    state: &mut BitchatState,
    peripheral: Option<&Peripheral>,
    cmd_char: Option<&btleplug::api::Characteristic>,
) {
    // Handle channel switches
    if let Some(channel_name) = app.pending_channel_switch.take() {
        if channel_name == "#public" {
            state.chat_context.switch_to_public();
        } else {
            state.chat_context.switch_to_channel(&channel_name);
        }
    }
    
    // Handle DM switches
    if let Some((target_nickname, _)) = app.pending_dm_switch.take() {
        let peer_id = {
            let peers = state.peers.lock().await;
            peers.iter()
                .find(|(_, peer)| peer.nickname.as_deref() == Some(&target_nickname))
                .map(|(id, _)| id.clone())
        };
        
        if let Some(target_peer_id) = peer_id {
            state.chat_context.enter_dm_mode(&target_nickname, &target_peer_id);
        }
    }
    
    // Handle nickname updates
    if let Some(new_nickname) = app.pending_nickname_update.take() {
        state.nickname = new_nickname.clone();
        app.nickname = new_nickname.clone();
        
        // Announce new nickname
        if let (Some(peripheral), Some(cmd_char)) = (peripheral, cmd_char) {
            let announce_packet = create_bitchat_packet(
                &state.my_peer_id,
                MessageType::Announce,
                new_nickname.as_bytes().to_vec(),
            );
            let _ = peripheral.write(cmd_char, &announce_packet, WriteType::WithoutResponse).await;
        }
        
        // Save state
        if let Err(e) = state.save() {
            error!("Failed to save state after nickname change: {}", e);
        }
        
        app.add_log_message(format!("system: Nickname changed to: {}", new_nickname));
    }
    
    // Handle conversation clear
    if app.pending_clear_conversation {
        app.pending_clear_conversation = false;
        app.clear_current_conversation();
        
        let context_msg = match &state.chat_context.current_mode {
            ChatMode::Public => "Cleared public chat".to_string(),
            ChatMode::Channel(channel) => format!("Cleared channel {}", channel),
            ChatMode::PrivateDM { nickname, .. } => format!("Cleared DM with {}", nickname),
        };
        app.add_log_message(format!("system: {}", context_msg));
    }
}

async fn handle_user_input(
    line: &str,
    state: &mut BitchatState,
    app: &mut App,
    peripheral: Option<&Peripheral>,
    cmd_char: Option<&btleplug::api::Characteristic>,
    ui_tx: &mpsc::Sender<String>,
) -> Result<()> {
    // Handle exit command
    if line.trim() == "/exit" {
        app.should_quit = true;
        return Ok(());
    }
    
    // Ensure connection for commands that require it
    if !app.connected && !line.starts_with("/help") && !line.starts_with("/exit") {
        app.add_log_message("system: Please wait for Bluetooth connection to be established.".to_string());
        return Ok(());
    }
    
    // Handle help command
    if line == "/help" {
        let help_text = terminal_ux::get_help_text();
        for line in help_text.lines() {
            let trimmed = line.trim();
            if !trimmed.is_empty() {
                app.add_log_message(format!("system: {}", trimmed));
            }
        }
        return Ok(());
    }
    
    // Route command to appropriate handler
    // (Implementation would call the existing command handlers)
    
    Ok(())
}

async fn handle_telepathy_message(
    msg: serde_json::Value,
    state: &BitchatState,
    peripheral: Option<&Peripheral>,
    cmd_char: Option<&btleplug::api::Characteristic>,
    ui_tx: &mpsc::Sender<String>,
) {
    debug!("Processing telepathy message: {}", msg);
    
    if let (Some(peripheral), Some(cmd_char)) = (peripheral, cmd_char) {
        let payload = msg.to_string();
        let packet = create_bitchat_packet(
            &state.my_peer_id,
            MessageType::Telepathy,
            payload.as_bytes().to_vec(),
        );
        
        match peripheral.write(cmd_char, &packet, WriteType::WithoutResponse).await {
            Ok(_) => {
                debug!("Telepathy message sent successfully");
                let _ = ui_tx.send(format!("[TELEPATHY] Outbound mesh signal shared: {} 📡", payload)).await;
            }
            Err(e) => {
                error!("Failed to send telepathy message: {}", e);
            }
        }
    } else {
        warn!("Cannot send telepathy message: Bluetooth not connected");
    }
}

// ============================================================================
// Tests
// ============================================================================

#[cfg(test)]
mod tests {
    use super::*;

    #[test]
    fn test_message_type_values() {
        assert_eq!(MessageType::Announce as u8, 0x01);
        assert_eq!(MessageType::KeyExchange as u8, 0x02);
        assert_eq!(MessageType::Leave as u8, 0x03);
        assert_eq!(MessageType::Message as u8, 0x04);
    }

    #[test]
    fn test_bitchat_state_initialization() {
        let state = BitchatState::new();
        assert!(state.is_ok());
        
        let state = state.unwrap();
        assert!(!state.my_peer_id.is_empty());
        assert!(!state.nickname.is_empty());
    }
}
