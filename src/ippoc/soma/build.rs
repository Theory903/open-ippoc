use std::io::Result;
fn main() -> Result<()> {
    tonic_build::compile_protos("proto/body.proto")?;
    tonic_build::compile_protos("proto/two_tower.proto")?;
    Ok(())
}