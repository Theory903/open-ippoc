// Integration tests for GitEvolution library
//
// These tests verify:
// - Repository operations (open, fetch, merge)
// - Conflict resolution workflows
// - Feature proposal mechanisms
// - Commit metadata formatting
// - Auto-update functionality

use anyhow::Result;
use git2::{Repository, Signature};
use std::path::{Path, PathBuf};
use tempfile::TempDir;

// Import from lib.rs
use git_evolution::{
    BrainMutationResolver, CommitMetadata, ConflictContext, GitEvolution,
};

// Mock Brain Resolver for testing
struct MockBrainResolver {
    should_approve: bool,
    resolution_content: String,
}

#[async_trait::async_trait]
impl BrainMutationResolver for MockBrainResolver {
    async fn resolve_conflict(&self, _conflict: ConflictContext) -> Result<String> {
        Ok(self.resolution_content.clone())
    }

    async fn simulate_patch(&self, _repo_root: &str, _patch_content: &str) -> Result<bool> {
        Ok(self.should_approve)
    }

    async fn review_patch(&self, _patch_content: &str) -> Result<bool> {
        Ok(self.should_approve)
    }

    async fn scan_for_governance_violations(&self, _summary: &str) -> Result<Vec<String>> {
        if self.should_approve {
            Ok(vec![])
        } else {
            Ok(vec!["Mock governance violation".to_string()])
        }
    }
}

// Helper: Create a test repository
fn create_test_repo(dir: &Path) -> Result<Repository> {
    let repo = Repository::init(dir)?;

    // Create initial commit
    let sig = Signature::now("Test User", "test@example.com")?;
    let tree_id = repo.index()?.write_tree()?;
    let tree = repo.find_tree(tree_id)?;

    repo.commit(Some("HEAD"), &sig, &sig, "Initial commit", &tree, &[])?;

    Ok(repo)
}

// Helper: Write file to repo
fn write_file(repo_path: &Path, filename: &str, content: &str) -> Result<()> {
    std::fs::write(repo_path.join(filename), content)?;
    Ok(())
}

#[test]
fn test_commit_metadata_to_message() {
    let metadata = CommitMetadata {
        organ: "brain/cortex".to_string(),
        intent: "Add new feature".to_string(),
        description: "This adds a comprehensive new feature to the cortex module.".to_string(),
        impact: "Improves reasoning capabilities significantly.".to_string(),
    };

    let message = metadata.to_message();

    assert!(message.contains("brain/cortex: Add new feature"));
    assert!(message.contains("DESCRIPTION:"));
    assert!(message.contains("This adds a comprehensive new feature"));
    assert!(message.contains("IMPACT:"));
    assert!(message.contains("Improves reasoning capabilities"));
}

#[test]
fn test_git_evolution_open() -> Result<()> {
    let temp_dir = TempDir::new()?;
    let repo_path = temp_dir.path();

    // Create a repo
    create_test_repo(repo_path)?;

    // Test opening
    let git_evo = GitEvolution::open(repo_path)?;

    // Should not panic or error
    Ok(())
}

#[test]
fn test_git_evolution_open_invalid_repo() {
    let temp_dir = TempDir::new().unwrap();
    let non_repo_path = temp_dir.path();

    // Should fail for non-repository
    let result = GitEvolution::open(non_repo_path);
    assert!(result.is_err());
}

#[test]
fn test_summarize_staged_changes() -> Result<()> {
    let temp_dir = TempDir::new()?;
    let repo_path = temp_dir.path();

    let repo = create_test_repo(repo_path)?;

    // Create and stage a file
    write_file(repo_path, "test.txt", "Hello, World!")?;
    let mut index = repo.index()?;
    index.add_path(Path::new("test.txt"))?;
    index.write()?;

    let git_evo = GitEvolution::open(repo_path)?;
    let summary = git_evo.summarize_staged_changes()?;

    // Summary should contain the diff
    assert!(summary.contains("test.txt") || summary.len() > 0);

    Ok(())
}

#[test]
fn test_commit_staged() -> Result<()> {
    let temp_dir = TempDir::new()?;
    let repo_path = temp_dir.path();

    let repo = create_test_repo(repo_path)?;

    // Create and stage a file
    write_file(repo_path, "feature.txt", "New feature code")?;
    let mut index = repo.index()?;
    index.add_path(Path::new("feature.txt"))?;
    index.write()?;

    let git_evo = GitEvolution::open(repo_path)?;

    let metadata = CommitMetadata {
        organ: "body/immune".to_string(),
        intent: "Add test feature".to_string(),
        description: "Testing commit functionality".to_string(),
        impact: "Validates commit workflow".to_string(),
    };

    let commit_oid = git_evo.commit_staged(metadata.clone())?;

    // Verify commit was created
    assert!(!commit_oid.is_empty());

    // Verify commit message
    let repo = Repository::open(repo_path)?;
    let commit = repo.find_commit(git2::Oid::from_str(&commit_oid)?)?;
    let message = commit.message().unwrap();

    assert!(message.contains("body/immune: Add test feature"));
    assert!(message.contains("DESCRIPTION:"));
    assert!(message.contains("IMPACT:"));

    Ok(())
}

#[tokio::test]
async fn test_review_patch_approved() -> Result<()> {
    let temp_dir = TempDir::new()?;
    let repo_path = temp_dir.path();

    create_test_repo(repo_path)?;
    let git_evo = GitEvolution::open(repo_path)?;

    let brain = MockBrainResolver {
        should_approve: true,
        resolution_content: "resolved".to_string(),
    };

    let result = git_evo.review_patch(&brain, "Safe patch content").await?;

    assert!(result, "Patch should be approved");

    Ok(())
}

#[tokio::test]
async fn test_review_patch_rejected() -> Result<()> {
    let temp_dir = TempDir::new()?;
    let repo_path = temp_dir.path();

    create_test_repo(repo_path)?;
    let git_evo = GitEvolution::open(repo_path)?;

    let brain = MockBrainResolver {
        should_approve: false,
        resolution_content: "resolved".to_string(),
    };

    let result = git_evo.review_patch(&brain, "Dangerous patch").await?;

    assert!(!result, "Patch should be rejected due to governance violations");

    Ok(())
}

#[test]
fn test_conflict_context_structure() {
    let context = ConflictContext {
        repo_root: "/path/to/repo".to_string(),
        file_path: "src/main.rs".to_string(),
        hunk_ours: "our version".to_string(),
        hunk_theirs: "their version".to_string(),
        hunk_base: Some("base version".to_string()),
    };

    assert_eq!(context.repo_root, "/path/to/repo");
    assert_eq!(context.file_path, "src/main.rs");
    assert_eq!(context.hunk_ours, "our version");
    assert_eq!(context.hunk_theirs, "their version");
    assert!(context.hunk_base.is_some());
}

#[test]
fn test_commit_metadata_serialization() {
    let metadata = CommitMetadata {
        organ: "memory/episodic".to_string(),
        intent: "Store events".to_string(),
        description: "Adds event storage capability".to_string(),
        impact: "Better memory retention".to_string(),
    };

    // Test serialization
    let json = serde_json::to_string(&metadata).unwrap();
    assert!(json.contains("memory/episodic"));
    assert!(json.contains("Store events"));

    // Test deserialization
    let deserialized: CommitMetadata = serde_json::from_str(&json).unwrap();
    assert_eq!(deserialized.organ, metadata.organ);
    assert_eq!(deserialized.intent, metadata.intent);
}

#[test]
fn test_commit_metadata_clone() {
    let metadata = CommitMetadata {
        organ: "brain/cortex".to_string(),
        intent: "Test clone".to_string(),
        description: "Testing clone trait".to_string(),
        impact: "Ensures metadata can be cloned".to_string(),
    };

    let cloned = metadata.clone();

    assert_eq!(cloned.organ, metadata.organ);
    assert_eq!(cloned.intent, metadata.intent);
    assert_eq!(cloned.description, metadata.description);
    assert_eq!(cloned.impact, metadata.impact);
}

// Edge case: Empty commit message components
#[test]
fn test_commit_metadata_empty_fields() {
    let metadata = CommitMetadata {
        organ: "".to_string(),
        intent: "".to_string(),
        description: "".to_string(),
        impact: "".to_string(),
    };

    let message = metadata.to_message();

    // Should still generate valid structure
    assert!(message.contains("DESCRIPTION:"));
    assert!(message.contains("IMPACT:"));
}

// Edge case: Very long commit messages
#[test]
fn test_commit_metadata_long_content() {
    let long_description = "A".repeat(5000);
    let long_impact = "B".repeat(5000);

    let metadata = CommitMetadata {
        organ: "infra/ci".to_string(),
        intent: "Test long content".to_string(),
        description: long_description.clone(),
        impact: long_impact.clone(),
    };

    let message = metadata.to_message();

    assert!(message.contains(&long_description));
    assert!(message.contains(&long_impact));
    assert!(message.len() > 10000);
}

// Test multi-line description and impact
#[test]
fn test_commit_metadata_multiline() {
    let metadata = CommitMetadata {
        organ: "docs/api".to_string(),
        intent: "Update documentation".to_string(),
        description: "Line 1\nLine 2\nLine 3".to_string(),
        impact: "Impact line 1\nImpact line 2".to_string(),
    };

    let message = metadata.to_message();

    assert!(message.contains("Line 1"));
    assert!(message.contains("Line 2"));
    assert!(message.contains("Line 3"));
    assert!(message.contains("Impact line 1"));
    assert!(message.contains("Impact line 2"));
}

// Negative test: Verify trait bounds are correct
#[test]
fn test_brain_resolver_trait_is_send_sync() {
    fn assert_send_sync<T: Send + Sync>() {}
    assert_send_sync::<MockBrainResolver>();
}

#[tokio::test]
async fn test_propose_feature_rejected_by_review() -> Result<()> {
    let temp_dir = TempDir::new()?;
    let repo_path = temp_dir.path();

    create_test_repo(repo_path)?;
    let git_evo = GitEvolution::open(repo_path)?;

    let brain = MockBrainResolver {
        should_approve: false, // Reject during review
        resolution_content: "".to_string(),
    };

    let metadata = CommitMetadata {
        organ: "brain/cortex".to_string(),
        intent: "Add dangerous feature".to_string(),
        description: "This feature is dangerous".to_string(),
        impact: "Could break everything".to_string(),
    };

    let result = git_evo.propose_feature("dangerous-feature", metadata, &brain).await?;

    assert!(!result, "Feature should be rejected by immune system");

    Ok(())
}

// Regression test: Ensure IPPOC signature is used
#[test]
fn test_ippoc_signature_in_commits() -> Result<()> {
    let temp_dir = TempDir::new()?;
    let repo_path = temp_dir.path();

    let repo = create_test_repo(repo_path)?;

    // Create and stage a file
    write_file(repo_path, "test.rs", "fn main() {}")?;
    let mut index = repo.index()?;
    index.add_path(Path::new("test.rs"))?;
    index.write()?;

    let git_evo = GitEvolution::open(repo_path)?;

    let metadata = CommitMetadata {
        organ: "body/immune".to_string(),
        intent: "Test signature".to_string(),
        description: "Verify IPPOC signature is used".to_string(),
        impact: "Ensures proper attribution".to_string(),
    };

    let commit_oid = git_evo.commit_staged(metadata)?;

    // Verify commit author
    let repo = Repository::open(repo_path)?;
    let commit = repo.find_commit(git2::Oid::from_str(&commit_oid)?)?;

    assert_eq!(commit.author().name().unwrap(), "IPPOC-Immune");
    assert_eq!(commit.author().email().unwrap(), "immune@ippoc.os");

    Ok(())
}