use anyhow::Result;
use quinn::{Endpoint, ServerConfig, ClientConfig};
use std::net::SocketAddr;
use std::sync::Arc;
use tokio::sync::mpsc;
use tracing::info;
use crate::discovery::Discovery;

pub struct NervousSystemTransport {
    endpoint: Endpoint,
    rx_channel: mpsc::Receiver<Vec<u8>>,
    discovery: Arc<Discovery>,
}

impl NervousSystemTransport {
    pub async fn bind(port: u16, discovery: Arc<Discovery>) -> Result<Self> {
        let (server_config, client_config) = configure_quic()?;
        
        let addr = SocketAddr::from(([0, 0, 0, 0], port));
        let mut endpoint = Endpoint::server(server_config, addr)?;
        endpoint.set_default_client_config(client_config);
        
        info!("NervousSystem: Listening on QUIC port {}", port);
        
        let (tx, rx) = mpsc::channel(100);
        
        // Spawn listener
        let endpoint_clone = endpoint.clone();
        let tx_clone = tx.clone();
        tokio::spawn(async move {
            while let Some(conn) = endpoint_clone.accept().await {
                info!("NervousSystem: Incoming connection from {}", conn.remote_address());
                // Handle connection
                let tx = tx_clone.clone();
                tokio::spawn(async move {
                    if let Ok((mut send, mut recv)) = conn.accept_bi().await {
                        while let Ok(data) = recv.read_chunk(usize::MAX, true).await {
                            if let Some(chunk) = data {
                                let buffer = chunk.bytes.to_vec();
                                if let Err(e) = tx.send(buffer).await {
                                    info!("NervousSystem: Failed to send received data: {}", e);
                                    break;
                                }
                            }
                        }
                    }
                });
            }
        });

        Ok(Self {
            endpoint,
            rx_channel: rx,
            discovery,
        })
    }

    pub async fn send_thought(&self, target: SocketAddr, data: &[u8]) -> Result<()> {
        let conn = self.endpoint.connect(target, "ippoc-node")?.await?;
        let (mut send, _) = conn.open_bi().await?;
        send.write_all(data).await?;
        send.finish().await?;
        Ok(())
    }

    pub async fn send_broadcast(&self, data: &[u8]) -> Result<()> {
        let peers = self.discovery.get_peers();
        info!("NervousSystem: Broadcasting to {} peers", peers.len());
        
        for (_, ip) in peers.iter() {
            let target = SocketAddr::new(*ip, self.endpoint.local_addr()?.port());
            if let Err(e) = self.send_thought(target, data).await {
                info!("NervousSystem: Failed to send to peer {}: {}", target, e);
            }
        }
        
        Ok(())
    }

    /// Receive the next thought/message from the nervous system
    pub async fn receive(&mut self) -> Option<Vec<u8>> {
        self.rx_channel.recv().await
    }

    pub fn get_discovered_peers(&self) -> Vec<SocketAddr> {
        let peers = self.discovery.get_peers();
        peers.iter()
            .map(|(_, ip)| SocketAddr::new(*ip, self.endpoint.local_addr().unwrap().port()))
            .collect()
    }
}

fn configure_quic() -> Result<(ServerConfig, ClientConfig)> {
    // Generate self-signed cert for P2P
    let cert = rcgen::generate_simple_self_signed(vec!["ippoc-node".into()])?;
    let cert_der = cert.serialize_der()?;
    let priv_key = cert.serialize_private_key_der();
    
    // rustls 0.21 API
    let priv_key = rustls::PrivateKey(priv_key);
    let cert_chain = vec![rustls::Certificate(cert_der.clone())];

    let server_config = ServerConfig::with_single_cert(cert_chain.clone(), priv_key)?;
    
    // Client config with custom verifier for P2P
    let crypto = rustls::ClientConfig::builder()
        .with_safe_defaults()
        .with_custom_certificate_verifier(Arc::new(SkipServerVerification))
        .with_no_client_auth();

    let client_config = ClientConfig::new(Arc::new(crypto));

    Ok((server_config, client_config))
}

struct SkipServerVerification;

impl rustls::client::ServerCertVerifier for SkipServerVerification {
    fn verify_server_cert(
        &self,
        _end_entity: &rustls::Certificate,
        _intermediates: &[rustls::Certificate],
        _server_name: &rustls::ServerName,
        _scts: &mut dyn Iterator<Item = &[u8]>,
        _ocsp_response: &[u8],
        _now: std::time::SystemTime,
    ) -> Result<rustls::client::ServerCertVerified, rustls::Error> {
        Ok(rustls::client::ServerCertVerified::assertion())
    }
}
