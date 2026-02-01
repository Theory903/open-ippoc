use anyhow::{Result, Context, anyhow};
use git2::{Repository, Signature, MergeOptions, AnnotatedCommit};
use std::path::{Path, PathBuf};
use tracing::{info, warn, error};
use serde::{Deserialize, Serialize};

/// Interface for the Brain's reasoning engine to resolve code mutations
#[async_trait::async_trait]
pub trait BrainMutationResolver: Send + Sync {
    async fn resolve_conflict(&self, conflict: ConflictContext) -> Result<String>;
    async fn simulate_patch(&self, repo_root: &str, patch_content: &str) -> Result<bool>;
}

#[derive(Debug, Serialize, Deserialize, Clone)]
pub struct CommitMetadata {
    pub organ: String,
    pub intent: String,
    pub description: String,
    pub impact: String,
}

impl CommitMetadata {
    pub fn to_message(&self) -> String {
        format!(
            "{}: {}\n\nDESCRIPTION:\n{}\n\nIMPACT:\n{}",
            self.organ, self.intent, self.description, self.impact
        )
    }
}

#[derive(Debug, Serialize, Deserialize)]
pub struct ConflictContext {
    pub repo_root: String,
    pub file_path: String,
    pub hunk_ours: String,
    pub hunk_theirs: String,
    pub hunk_base: Option<String>,
}

pub struct GitEvolution {
    path: PathBuf,
}

impl GitEvolution {
    /// Open an existing repository
    pub fn open<P: AsRef<Path>>(path: P) -> Result<Self> {
        let repo_path = path.as_ref().to_path_buf();
        // Verify it's a repo
        Repository::open(&repo_path)?;
        Ok(Self { path: repo_path })
    }

    /// Autonomous Update Cycle
    pub async fn auto_update<T>(&self, remote_name: &str, branch: &str, brain: &T) -> Result<bool> 
    where 
        T: BrainMutationResolver + 'static + ?Sized
    {
        info!("GitEvolution: Checking for updates from {}/{}", remote_name, branch);

        // 1. Fetch & Analyze (Synchronous block to avoid Holding Repo across Await)
        let (analysis, remote_commit_id, branch_ref_name) = {
            let repo = Repository::open(&self.path)?;
            self.fetch_upstream(&repo, remote_name, branch)?;

            let head = repo.head()?;
            let branch_ref = head.name().ok_or_else(|| anyhow!("Detached HEAD"))?.to_string();

            let remote_ref_name = format!("refs/remotes/{}/{}", remote_name, branch);
            let remote_commit = repo.find_reference(&remote_ref_name)?
                .peel_to_commit()?;

            let local_commit = head.peel_to_commit()?;

            if local_commit.id() == remote_commit.id() {
                info!("GitEvolution: Already up to date.");
                return Ok(true);
            }

            let annotated_remote = repo.find_annotated_commit(remote_commit.id())?;
            let (analysis, _) = repo.merge_analysis(&[&annotated_remote])?;
            
            (analysis, remote_commit.id(), branch_ref)
        };

        if analysis.is_fast_forward() {
             let repo = Repository::open(&self.path)?;
             let remote_commit = repo.find_commit(remote_commit_id)?;
             self.perform_fast_forward(&repo, &branch_ref_name, &remote_commit)?;
             info!("GitEvolution: Fast-forward update successful.");
             Ok(true)
        } else if analysis.is_normal() {
             let has_conflicts = {
                 let repo = Repository::open(&self.path)?;
                 let annotated_remote = repo.find_annotated_commit(remote_commit_id)?;
                 let mut merge_opts = MergeOptions::new();
                 repo.merge(&[&annotated_remote], Some(&mut merge_opts), None)?;
                 
                 repo.index()?.has_conflicts()
             }; 
             
             if has_conflicts {
                 warn!("GitEvolution: CONFLICT DETECTED. Invoking Brain...");
                 self.resolve_conflicts_with_brain(brain).await
             } else {
                let repo = Repository::open(&self.path)?;
                let annotated_remote = repo.find_annotated_commit(remote_commit_id)?;
                let metadata = CommitMetadata {
                    organ: "body/immune".to_string(),
                    intent: "Sync with upstream".to_string(),
                    description: "Autonomous update from remote tracking branch".to_string(),
                    impact: "Keep local node code in sync with evolution source".to_string(),
                };
                self.finalize_merge(&repo, &annotated_remote, &metadata)?;
                 info!("GitEvolution: Clean merge successful.");
                 Ok(true)
             }
        } else {
            info!("GitEvolution: No actions required for update.");
            Ok(true)
        }
    }

    fn fetch_upstream(&self, repo: &Repository, remote: &str, branch: &str) -> Result<()> {
        let mut remote = repo.find_remote(remote)?;
        remote.fetch(&[branch], None, None).context("Failed to fetch upstream")?;
        Ok(())
    }

    fn perform_fast_forward(&self, repo: &Repository, refname: &str, target: &git2::Commit) -> Result<()> {
        let mut reference = repo.find_reference(refname)?;
        reference.set_target(target.id(), "Fast-Forward")?;
        repo.set_head(refname)?;
        repo.checkout_head(Some(git2::build::CheckoutBuilder::default().force()))?;
        Ok(())
    }

    fn finalize_merge(&self, repo: &Repository, remote_commit: &AnnotatedCommit, metadata: &CommitMetadata) -> Result<()> {
        let signature = Signature::now("IPPOC-Immune", "immune@ippoc.os")?;
        let tree_id = repo.index()?.write_tree()?;
        let tree = repo.find_tree(tree_id)?;
        let parent = repo.head()?.peel_to_commit()?;
        let remote = repo.find_commit(remote_commit.id())?;

        let msg = metadata.to_message();

        repo.commit(
            Some("HEAD"),
            &signature,
            &signature,
            &msg,
            &tree,
            &[&parent, &remote]
        )?;
        Ok(())
    }

    /// Extracted Immune Response: Conflict -> Hunks -> Brain -> Patch -> Resolution
    async fn resolve_conflicts_with_brain<T>(&self, brain: &T) -> Result<bool> 
    where 
        T: BrainMutationResolver + ?Sized
    {
        // 1. Gather Conflicts
        let conflict_contexts = {
            let repo = Repository::open(&self.path)?;
            let index = repo.index()?;
            let conflicts = index.conflicts()?;
            
            let mut contexts = Vec::new();
            for conflict_res in conflicts {
                let conflict = conflict_res?;
                let mut context = ConflictContext {
                repo_root: self.path.to_string_lossy().to_string(),
                file_path: String::new(),
                hunk_ours: String::new(),
                hunk_theirs: String::new(),
                hunk_base: None,
            };

                if let Some(ref ours) = conflict.our {
                     context.file_path = String::from_utf8_lossy(&ours.path).to_string();
                     context.hunk_ours = self.read_blob_content(&repo, ours.id)?;
                }
                if let Some(ref theirs) = conflict.their {
                     context.hunk_theirs = self.read_blob_content(&repo, theirs.id)?;
                }
                if let Some(ref base) = conflict.ancestor {
                     context.hunk_base = Some(self.read_blob_content(&repo, base.id)?);
                }
                contexts.push(context);
            }
            contexts
        };

        let mut resolutions = Vec::new();
        for context in conflict_contexts {
            info!("GitEvolution: Requesting resolution for {}", context.file_path);
            let file_path = context.file_path.clone();
            let resolution = brain.resolve_conflict(context).await?;
            resolutions.push((file_path, resolution));
        }

        // 2. Apply Resolutions
        {
            let repo = Repository::open(&self.path)?;
            for (path, resolution) in resolutions {
                 self.apply_resolution(&repo, &path, &resolution)?;
            }

            let mut index = repo.index()?;
            if index.has_conflicts() {
                 error!("GitEvolution: Brain failed to resolve some conflicts. Aborting merge.");
                 repo.cleanup_state()?; 
                 return Ok(false);
            }
            index.write()?;
        }

        // 3. Simulation Step
        info!("GitEvolution: Conflict resolved, running simulation...");
        
        if brain.simulate_patch(&self.path.to_string_lossy(), "conflict_resolution").await? {
             info!("GitEvolution: Resolution verified by simulation. Finalizing.");
             let repo = Repository::open(&self.path)?;
             let mut index = repo.index()?;
             let head_commit = repo.head()?.peel_to_commit()?;
             let merge_head = repo.find_reference("MERGE_HEAD")?.peel_to_commit()?;
             
             let signature = Signature::now("IPPOC-Immune", "immune@ippoc.os")?;
             let tree_id = index.write_tree()?;
             let tree = repo.find_tree(tree_id)?;

             let metadata = CommitMetadata {
                 organ: "body/immune".to_string(),
                 intent: "Resolve merge conflicts".to_string(),
                 description: "Brain Mutation Resolver successfully addressed file conflicts.".to_string(),
                 impact: "Merged evolutionary changes while maintaining structural integrity.".to_string(),
             };
             let msg = metadata.to_message();

             repo.commit(
                 Some("HEAD"),
                 &signature,
                 &signature,
                 &msg,
                 &tree,
                 &[&head_commit, &merge_head]
             )?;
             
             repo.cleanup_state()?;
             Ok(true)
        } else {
             warn!("GitEvolution: Simulation FAILED for resolution. Rolling back.");
             let repo = Repository::open(&self.path)?;
             repo.cleanup_state()?;
             Ok(false)
        }
    }

    fn read_blob_content(&self, repo: &Repository, id: git2::Oid) -> Result<String> {
        let blob = repo.find_blob(id)?;
        Ok(String::from_utf8_lossy(blob.content()).to_string())
    }

    fn apply_resolution(&self, repo: &Repository, path: &str, resolution: &str) -> Result<()> {
        let full_path = self.path.join(path);
        info!("GitEvolution: Applying resolution to {:?}", full_path);
        
        // 1. Write content to disk
        std::fs::write(&full_path, resolution)
            .context(format!("Failed to write resolution to {:?}", full_path))?;

        // 2. Add to Git Index
        let mut index = repo.index()?;
        index.add_path(Path::new(path))?;
        index.write()?;
        
        Ok(())
    }

    /// Propose a new patch for self-evolution (Manual Trigger)
    pub async fn propose_feature<T>(&self, feature_name: &str, metadata: CommitMetadata, brain: &T) -> Result<bool> 
    where 
        T: BrainMutationResolver + 'static + ?Sized
    {
        let safe_name = feature_name.replace(' ', "-").to_lowercase();
        let branch_name = format!("feature/{}", safe_name);
        info!("GitEvolution: Creating feature branch '{}'", branch_name);

        let (head_name, head_oid) = {
            let repo = Repository::open(&self.path)?;
            let head = repo.head()?;
            let head_commit = head.peel_to_commit()?;
            
            // Create branch if not exists, otherwise just use it
            if let Err(_) = repo.find_branch(&branch_name, git2::BranchType::Local) {
                repo.branch(&branch_name, &head_commit, false)?;
            }
            
            let head_name = head.name().unwrap_or("refs/heads/main").to_string();
            (head_name, head_commit.id())
        };

        // Checkout the feature branch
        {
            let repo = Repository::open(&self.path)?;
            let obj = repo.revparse_single(&format!("refs/heads/{}", branch_name))?;
            repo.checkout_tree(&obj, None)?;
            repo.set_head(&format!("refs/heads/{}", branch_name))?;
        }

        // 1. Simulate the patch on the feature branch
        if brain.simulate_patch(&self.path.to_string_lossy(), &metadata.description).await? {
             info!("GitEvolution: Feature PASSED simulation. Merging back to head.");
             
             let repo = Repository::open(&self.path)?;
             
             // Commit the changes to the feature branch first
             let signature = Signature::now("IPPOC-Immune", "immune@ippoc.os")?;
             let mut index = repo.index()?;
             let tree_id = index.write_tree()?;
             let tree = repo.find_tree(tree_id)?;
             let parent = repo.head()?.peel_to_commit()?;
             
             repo.commit(
                 Some("HEAD"),
                 &signature,
                 &signature,
                 &metadata.to_message(),
                 &tree,
                 &[&parent]
             )?;

             // Reset to original head and merge
             let head_obj = repo.find_object(head_oid, None)?;
             repo.checkout_tree(&head_obj, None)?;
             repo.set_head(&head_name)?;
             
             let feature_ref = repo.find_reference(&format!("refs/heads/{}", branch_name))?;
             let feature_annotated = repo.find_annotated_commit(feature_ref.peel_to_commit()?.id())?;
             
             let (analysis, _) = repo.merge_analysis(&[&feature_annotated])?;
             
             if analysis.is_fast_forward() {
                  self.perform_fast_forward(&repo, &head_name, &repo.find_commit(feature_annotated.id())?)?;
             } else {
                  let mut merge_opts = MergeOptions::new();
                  repo.merge(&[&feature_annotated], Some(&mut merge_opts), None)?;
                  self.finalize_merge(&repo, &feature_annotated, &metadata)?;
             }
             
             repo.cleanup_state()?;
             Ok(true)
        } else {
             warn!("GitEvolution: Feature FAILED simulation. Staying on branch for inspection.");
             Ok(false)
        }
    }

    /// Collect a summary of staged changes for the Brain to analyze
    pub fn summarize_staged_changes(&self) -> Result<String> {
        let repo = Repository::open(&self.path)?;
        let mut index = repo.index()?;
        let tree_id = index.write_tree()?;
        let tree = repo.find_tree(tree_id)?;
        
        let head = repo.head()?.peel_to_commit()?;
        let head_tree = head.tree()?;
        
        let diff = repo.diff_tree_to_tree(Some(&head_tree), Some(&tree), None)?;
        
        let mut summary = String::new();
        diff.print(git2::DiffFormat::Patch, |_delta, _hunk, line| {
            if let Ok(content) = std::str::from_utf8(line.content()) {
                summary.push_str(content);
            }
            true
        })?;
        
        Ok(summary)
    }

    /// Commit staged changes with metadata provided by the Brain
    pub fn commit_staged(&self, metadata: CommitMetadata) -> Result<String> {
        let repo = Repository::open(&self.path)?;
        let signature = Signature::now("IPPOC-Immune", "immune@ippoc.os")?;
        
        let mut index = repo.index()?;
        let tree_id = index.write_tree()?;
        let tree = repo.find_tree(tree_id)?;
        
        let head_commit = repo.head()?.peel_to_commit()?;
        let msg = metadata.to_message();
        
        let oid = repo.commit(
            Some("HEAD"),
            &signature,
            &signature,
            &msg,
            &tree,
            &[&head_commit]
        )?;
        
        Ok(oid.to_string())
    }
}

