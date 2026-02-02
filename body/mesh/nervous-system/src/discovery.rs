use anyhow::Result;
use mdns_sd::{ServiceDaemon, ServiceInfo};
use std::collections::HashMap;
use std::net::IpAddr;
use tracing::info;
use std::sync::{Arc, Mutex};

pub struct Discovery {
    mdns: ServiceDaemon,
    peers: Arc<Mutex<HashMap<String, IpAddr>>>,
}

impl Discovery {
    pub fn new() -> Result<Self> {
        let mdns = ServiceDaemon::new()?;
        Ok(Self {
            mdns,
            peers: Arc::new(Mutex::new(HashMap::new())),
        })
    }

    pub fn advertise(&self, port: u16) -> Result<()> {
        let unique_id = uuid::Uuid::new_v4().to_string();
        let service_type = "_ippoc._udp.local.";
        let instance_name = format!("node_{}", unique_id);
        let ip = "0.0.0.0"; // Will bind to all
        let host_name = format!("{}.local.", instance_name);

        let service_info = ServiceInfo::new(
            service_type,
            &instance_name,
            &host_name,
            ip,
            port,
            None,
        )?.enable_addr_auto();

        self.mdns.register(service_info)?;
        info!("NervousSystem: Advertising self as {}", instance_name);
        Ok(())
    }

    pub fn browse(&self) {
        // Start browsing for other nodes
        let service_type = "_ippoc._udp.local.";
        let receiver = self.mdns.browse(service_type).expect("Failed to browse");
        let peers = self.peers.clone();

        std::thread::spawn(move || {
            while let Ok(event) = receiver.recv() {
                match event {
                    mdns_sd::ServiceEvent::ServiceResolved(info) => {
                        info!("NervousSystem: Found peer at {:?}", info.get_addresses());
                         if let Some(ip) = info.get_addresses().iter().next() {
                            let mut p = peers.lock().unwrap();
                            p.insert(info.get_fullname().to_string(), *ip);
                        }
                    }
                    mdns_sd::ServiceEvent::ServiceRemoved(info) => {
                        info!("NervousSystem: Peer removed: {}", info.get_fullname());
                        let mut p = peers.lock().unwrap();
                        p.remove(&info.get_fullname().to_string());
                    }
                    _ => {}
                }
            }
        });
    }

    pub fn get_peers(&self) -> HashMap<String, IpAddr> {
        self.peers.lock().unwrap().clone()
    }

    pub fn peer_count(&self) -> usize {
        self.peers.lock().unwrap().len()
    }

    pub fn is_peer_available(&self, peer_id: &str) -> bool {
        self.peers.lock().unwrap().contains_key(peer_id)
    }
}
