pub mod transport;
pub mod discovery;

use anyhow::Result;
use transport::NervousSystemTransport;
use discovery::Discovery;

pub async fn connect(port: u16) -> Result<(NervousSystemTransport, Discovery)> {
    println!("NervousSystem: Initializing...");
    
    let transport = NervousSystemTransport::bind(port).await?;
    let discovery = Discovery::new()?;
    
    discovery.advertise(port)?;
    discovery.browse();

    Ok((transport, discovery))
}
