pub mod transport;
pub mod discovery;

use anyhow::Result;
use transport::NervousSystemTransport;
use discovery::Discovery;
use std::sync::Arc;

pub async fn connect(port: u16) -> Result<(NervousSystemTransport, Discovery)> {
    println!("NervousSystem: Initializing...");
    
    let discovery = Arc::new(Discovery::new()?);
    let transport = NervousSystemTransport::bind(port, discovery.clone()).await?;
    
    discovery.advertise(port)?;
    discovery.browse();

    Ok((transport, discovery))
}
