use std::io::Result;

fn main() -> Result<()> {
    println!("Current directory: {:?}", std::env::current_dir()?);
    
    // Create a temporary directory for output
    let temp_dir = tempfile::tempdir()?;
    println!("Output directory: {:?}", temp_dir.path());
    
    // Run tonic build
    tonic_build::configure()
        .out_dir(temp_dir.path())
        .compile(&["../proto/body.proto", "../proto/two_tower.proto"], &["../"])?;
    
    // List generated files
    println!("Generated files:");
    for entry in std::fs::read_dir(temp_dir.path())? {
        let entry = entry?;
        println!("  {:?}", entry.file_name());
    }
    
    Ok(())
}
