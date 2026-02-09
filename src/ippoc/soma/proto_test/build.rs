use std::io::Result;

fn main() -> Result<()> {
    println!("Current directory: {:?}", std::env::current_dir()?);
    
    let body_proto = "../proto/body.proto";
    let two_tower_proto = "../proto/two_tower.proto";
    
    println!("body.proto exists: {}", std::path::Path::new(body_proto).exists());
    println!("two_tower.proto exists: {}", std::path::Path::new(two_tower_proto).exists());
    
    tonic_build::compile_protos(body_proto)?;
    println!("body.proto compiled successfully");
    
    tonic_build::compile_protos(two_tower_proto)?;
    println!("two_tower.proto compiled successfully");
    
    Ok(())
}
