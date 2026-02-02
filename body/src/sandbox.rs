use anyhow::Result;
use wasmtime::{Config, Engine, Linker, Module, Store};
use wasmtime_wasi::WasiCtxBuilder;
use tracing::{info, warn};
use std::path::Path;

#[derive(Debug, Clone, Copy, PartialEq, Eq, serde::Serialize, serde::Deserialize)]
pub enum CapabilityToken {
    ReadDocs,
    NetworkAccess,
    KernelActuate,
}

#[allow(dead_code)]
#[derive(Clone)]
pub struct Sandbox {
    engine: Engine,
}

#[allow(dead_code)]
impl Sandbox {
    pub fn new() -> Result<Self> {
        let mut config = Config::new();
        config.async_support(true);
        config.consume_fuel(true); // Limit CPU
        
        let engine = Engine::new(&config)?;
        Ok(Self { engine })
    }

    pub async fn run_wasm(&self, wasm_bytes: &[u8], tokens: &[CapabilityToken], isolation_root: &Path) -> Result<()> {
        info!("Sandbox: Preparing to run WASM module with tokens: {:?} in {:?}", tokens, isolation_root);
        
        let mut linker = Linker::new(&self.engine);
        wasmtime_wasi::add_to_linker(&mut linker, |s| s)?;

        let mut builder = WasiCtxBuilder::new();
        builder.inherit_stdio();

        // Rule 2.3: Physical Isolation Law - Sandbox is chrooted to its isolation root
        builder.preopened_dir(
            cap_std::fs::Dir::open_ambient_dir(isolation_root, cap_std::ambient_authority())?,
            ".",
        )?;

        // Token-based enforcement
        for token in tokens {
            match token {
                CapabilityToken::ReadDocs => {
                    info!("Sandbox: Granting READ_DOCS (mapping docs/ role)");
                    builder.preopened_dir(
                        cap_std::fs::Dir::open_ambient_dir("docs", cap_std::ambient_authority())?,
                        "docs",
                    )?;
                }
                CapabilityToken::NetworkAccess => {
                    warn!("Sandbox: Granting NETWORK_ACCESS (High Risk)");
                    // In a real implementation, we would configure socket allowlists here
                }
                CapabilityToken::KernelActuate => {
                    warn!("Sandbox: Granting KERNEL_ACTUATE (Critical Risk)");
                }
            }
        }

        let wasi = builder.build();
            
        let mut store = Store::new(&self.engine, wasi);
        store.set_fuel(10_000_000)?; // Fuel limit (new API)

        let module = Module::new(&self.engine, wasm_bytes)?;
        linker.module_async(&mut store, "", &module).await?;
        
        let instance = linker.instantiate_async(&mut store, &module).await?;
        let run = instance.get_typed_func::<(), ()>(&mut store, "_start")?;
        
        info!("Sandbox: Executing...");
        run.call_async(&mut store, ()).await?;
        info!("Sandbox: Execution finished.");
        
        Ok(())
    }
}
