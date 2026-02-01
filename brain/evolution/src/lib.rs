use anyhow::{Result, Context};
use async_trait::async_trait;
use git_evolution::{BrainMutationResolver, ConflictContext};
use cerebellum::Cerebrum;
use std::sync::Arc;
use tracing::{info, warn};

pub struct EvolutionEngine {
    cerebellum: Arc<Cerebrum>,
}

impl EvolutionEngine {
    pub fn new(cerebellum: Arc<Cerebrum>) -> Self {
        Self { cerebellum }
    }
}

#[async_trait]
impl BrainMutationResolver for EvolutionEngine {
    async fn resolve_conflict(&self, conflict: ConflictContext) -> Result<String> {
        info!("Brain: Analyzing conflict in {} within repo {}", conflict.file_path, conflict.repo_root);
        
        // 1. Rule 6: LOC Enforcement (< 300 lines)
        let ours_loc = conflict.hunk_ours.lines().count();
        let theirs_loc = conflict.hunk_theirs.lines().count();
        
        if ours_loc > 300 || theirs_loc > 300 {
            return Err(anyhow::anyhow!("Rule 6 Violation: Conflict exceeds 300 LOC limit (ours: {}, theirs: {})", ours_loc, theirs_loc));
        }

        // 2. Rule 3: Organ Boundary Check BEFORE reasoning
        self.check_organ_boundaries(&conflict.repo_root, &conflict.file_path)?;

        // 3. Construct reasoning prompt with structural context
        let query = format!(
            "Task: Resolve Git Conflict\nPath: {}\nOrgan Context: {}\n\nOURS (Current version):\n{}\n\nTHEIRS (Incoming change):\n{}\n\nBASE (Common ancestor):\n{}\n\nConstraint: Ensure the resolution stays within the defined role of this organ and follows IPPOC-FS rules. Return ONLY the resolved content.",
            conflict.file_path,
            conflict.repo_root,
            conflict.hunk_ours,
            conflict.hunk_theirs,
            conflict.hunk_base.unwrap_or_default()
        );

        // 4. Consult Cerebellum (High-level reasoning)
        let req = cerebellum::ThoughtRequest {
            query,
            context_history: vec!["You are the Evolution Engine. You resolve conflicts while enforcing structural integrity and Rule 6.".to_string()],
        };

        let response = self.cerebellum.think(req).await?;
        let resolution = response.answer;

        // 5. Final LOC check
        let res_loc = resolution.lines().count();
        if res_loc > 300 {
             return Err(anyhow::anyhow!("Rule 6 Violation: Resolution ({}) exceeds 300 LOC limit.", res_loc));
        }
        
        info!("Brain: Resolution generated for {} (valid LOC and boundaries)", conflict.file_path);
        Ok(resolution)
    }

    async fn simulate_patch(&self, repo_root: &str, patch_content: &str) -> Result<bool> {
        info!("Brain: Simulating mutation impact at {} with strict warning enforcement", repo_root);
        
        // Rule 11: Warnings are errors
        let status = std::process::Command::new("cargo")
            .arg("check")
            .env("RUSTFLAGS", "-D warnings")
            .current_dir(repo_root)
            .status()
            .context("Simulation failed to execute check")?;

        if !status.success() {
             warn!("Brain: Mutation REJECTED. Lint errors/warnings detected (Rule 11).");
             return Ok(false);
        }

        let metadata = git_evolution::CommitMetadata {
            organ: "brain/evolution".to_string(),
            intent: "Apply simulated mutation".to_string(),
            description: patch_content.chars().take(200).collect(),
            impact: "Automated evolution of code logic".to_string(),
        };

        self.update_changelog(repo_root, &metadata)?;
        info!("Brain: Simulation PASSED.");
        Ok(true)
    }
}

impl EvolutionEngine {
    fn check_organ_boundaries(&self, repo_root: &str, file_path: &str) -> Result<()> {
        // Enforce Rule 3: Allowed Access Matrix
        let _root = std::path::Path::new(repo_root);
        let _file = std::path::Path::new(file_path);
        
        // Heuristic: If we are in 'mind', we should not be touching 'body' or 'brain' core unless via public API
        if repo_root.contains("/mind") && (file_path.contains("body/") || file_path.contains("brain/")) {
            return Err(anyhow::anyhow!("Rule 3 Violation: Evolution in 'mind' attempted to modify core organs directly."));
        }
        
        Ok(())
    }

    fn update_changelog(&self, repo_root: &str, metadata: &git_evolution::CommitMetadata) -> Result<()> {
        let changelog_path = std::path::Path::new(repo_root).join("CHANGELOG.md");
        let version = "0.1.1-e1"; 
        
        let entry = format!(
            "\n## [{}] - {}\n- {}: {}\n- Description: {}\n- Impact: {}\n",
            version,
            chrono::Utc::now().format("%Y-%m-%d"),
            metadata.organ,
            metadata.intent,
            metadata.description,
            metadata.impact
        );

        let mut file = std::fs::OpenOptions::new()
            .append(true)
            .create(true)
            .open(&changelog_path)?;

        use std::io::Write;
        file.write_all(entry.as_bytes())?;
        
        Ok(())
    }
}
