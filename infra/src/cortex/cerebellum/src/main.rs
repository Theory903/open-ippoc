use clap::{Parser, Subcommand};
use cerebellum::{Cerebrum, ThoughtRequest};
use hidb::HiDB;
use std::sync::Arc;
use tokio;

#[derive(Parser)]
#[command(name = "cerebellum")]
#[command(about = "The IPPOC Thinking Engine CLI", long_about = None)]
struct Cli {
    #[command(subcommand)]
    command: Commands,
}

#[derive(Subcommand)]
enum Commands {
    /// Deep thought on a query
    Think {
        query: String,
        #[arg(short, long)]
        context: Vec<String>,
    },
    /// Quick memory recall
    Recall {
        query: String,
    },
}

#[tokio::main]
async fn main() -> anyhow::Result<()> {
    // Initialize tracing
    tracing_subscriber::fmt::init();

    // 1. Boot HiDB (Postgres + Redis)
    let database_url = std::env::var("DATABASE_URL")
        .unwrap_or_else(|_| "postgresql://postgres:ippoc_secret@localhost:5432/ippoc_hidb".to_string());
    let redis_url =
        std::env::var("REDIS_URL").unwrap_or_else(|_| "redis://localhost:6379".to_string());
    let hidb = Arc::new(HiDB::connect(&database_url, &redis_url).await?);

    // 2. Boot Cerebrum
    let brain = Cerebrum::new(hidb);

    let cli = Cli::parse();

    match cli.command {
        Commands::Think { query, context } => {
            let req = ThoughtRequest {
                query,
                context_history: context,
            };
            let resp = cortex.think(req).await?;
            println!("{}", serde_json::to_string_pretty(&resp)?);
        }
        Commands::Recall { query } => {
            let memories = cortex.recall(&query).await?;
            println!("{}", serde_json::to_string_pretty(&memories)?);
        }
    }

    Ok(())
}
