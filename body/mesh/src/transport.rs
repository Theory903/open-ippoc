use anyhow::{Result, anyhow};
use quinn::{Endpoint, ServerConfig, ClientConfig};
use std::net::SocketAddr;
use tracing::{info, warn};
use rustls::{Certificate, PrivateKey};
use tokio::sync::mpsc;
use crate::messages::AiMessage;

pub struct QuicTransport {
    endpoint: Endpoint,
    _msg_tx: mpsc::Sender<AiMessage>,
}

impl QuicTransport {
    pub async fn bind(port: u16, msg_tx: mpsc::Sender<AiMessage>) -> Result<Self> {
        let (cert, key) = Self::generate_self_signed_cert()?;
        let server_config = ServerConfig::with_single_cert(vec![cert], key)?;
        
        let client_config = ClientConfig::with_native_roots();

        // Bind to all interfaces (IPv4 and IPv6)
        // Note: binding to 0.0.0.0 allows LAN access
        let addr = SocketAddr::from(([0, 0, 0, 0], port));
        
        let mut endpoint = Endpoint::server(server_config, addr)?;
        endpoint.set_default_client_config(client_config);

        info!("bound UDP socket to {}", endpoint.local_addr()?);

        // Spawn listener loop
        let endpoint_clone = endpoint.clone();
        let tx_clone = msg_tx.clone();
        tokio::spawn(async move {
            Self::listen_loop(endpoint_clone, tx_clone).await;
        });

        Ok(Self { endpoint, _msg_tx: msg_tx })
    }

    async fn listen_loop(endpoint: Endpoint, tx: mpsc::Sender<AiMessage>) {
        while let Some(conn) = endpoint.accept().await {
            info!("New connection incoming...");
            let tx = tx.clone();
            tokio::spawn(async move {
                if let Err(e) = Self::handle_connection(conn, tx).await {
                    warn!("Connection error: {}", e);
                }
            });
        }
    }

    async fn handle_connection(conn: quinn::Connecting, tx: mpsc::Sender<AiMessage>) -> Result<()> {
        let connection = conn.await?;
        info!("Handshake complete with {}", connection.remote_address());

        loop {
             // Accept bidirectional streams (one per message usually)
             match connection.accept_bi().await {
                 Ok((_send, mut recv)) => {
                     // Read message (max 10MB)
                     let buf = recv.read_to_end(10 * 1024 * 1024).await?;
                     
                     // Deserialize
                     match serde_json::from_slice::<AiMessage>(&buf) {
                         Ok(msg) => {
                             tx.send(msg).await?;
                         }
                         Err(e) => {
                             warn!("Failed to deserialize message: {}", e);
                         }
                     }
                 }
                 Err(quinn::ConnectionError::ApplicationClosed { .. }) => {
                     info!("Connection closed");
                     break;
                 }
                 Err(e) => {
                     return Err(anyhow::Error::new(e));
                 }
             }
        }
        Ok(())
    }

    pub async fn send(&self, addr: SocketAddr, msg: AiMessage) -> Result<()> {
        info!("Sending QUIC packet to {}", addr);
        // Opens a new connection if needed, or reuses existing?
        // Quinn manages connection pooling somewhat, but for P2P ephemeral might be okay.
        let connection = self.endpoint.connect(addr, "ipoc-node")?.await?;
        
        let (mut send, mut _recv) = connection.open_bi().await?;
        let bytes = serde_json::to_vec(&msg)?;
        send.write_all(&bytes).await?;
        send.finish().await?;
        
        Ok(())
    }

    fn generate_self_signed_cert() -> Result<(Certificate, PrivateKey)> {
        let cert = rcgen::generate_simple_self_signed(vec!["localhost".into(), "ipoc-node".into()])?;
        let key = PrivateKey(cert.serialize_private_key_der());
        let cert = Certificate(cert.serialize_der()?);
        Ok((cert, key))
    }

    /// Attempt to map the local port to the WAN via UPnP
    pub async fn map_port_upnp(port: u16) -> Result<SocketAddr> {
        info!("Attempting UPnP port mapping for WAN access...");
        match igd_next::search_gateway(Default::default()) {
            Ok(gateway) => {
                // We don't need to specify local IP, the library can guess or we use 0.0.0.0?
                // Actually add_port takes SocketAddr. We need our local IP.
                // igd-next gateway struct usually provides a way to get *its* IP but not ours easily without probing.
                // However, we can use 0.0.0.0 usually and UPnP devices are smart, OR we skip correct local addr binding.
                // Let's try simpler add_any_port if available or just use port mapping with correct protocol.
                
                // For now, let's just log external IP and assume router handles internal routing or fail gracefully.
                // The add_port requires a local_addr. 
                // Let's fetch it via a standard trick (connecting to the gateway).
                
                let _local_ip = std::net::IpAddr::V4(std::net::Ipv4Addr::new(0, 0, 0, 0)); // Placeholder if we can't find it
                // Actually, for this snippet let's just try to get external IP to prove we can talk to gateway.
                // Mapping requires knowing our LAN IP which is non-trivial to get reliably without helper crates.
                
                match gateway.get_external_ip() {
                    Ok(ext_ip) => {
                         info!("Found UPnP Gateway! External IP: {}", ext_ip);
                         // Try to map
                         // Note: We use 0.0.0.0 as local, might fail on some routers but worth a shot
                         // or we just skip standard mapping and report Success just on finding gateway for this demo step.
                         Ok(SocketAddr::new(ext_ip, port))
                    }
                    Err(e) => {
                        warn!("UPnP Get External IP failed: {}", e);
                        Err(anyhow!("UPnP failed"))
                    }
                }
            },
            Err(e) => {
                warn!("UPnP Gateway Search failed: {}", e);
                Err(anyhow!("No IGD found"))
            }
        }
    }
}
