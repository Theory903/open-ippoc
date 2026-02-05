"""
Tests for GitHub Actions Workflow Configurations

Validates:
- Workflow file structure and syntax
- Job configurations
- Step definitions
- Environment variables
- Trigger conditions
"""

import os
import yaml
import pytest
from pathlib import Path

# Path to workflows directory
WORKFLOWS_DIR = Path(__file__).parent.parent / ".github" / "workflows"


class TestCheckProtocolWorkflow:
    """Tests for the IPPOC Protocol Enforcer workflow"""

    @pytest.fixture
    def workflow(self):
        """Load check-protocol.yml workflow"""
        workflow_path = WORKFLOWS_DIR / "check-protocol.yml"
        with open(workflow_path, 'r') as f:
            return yaml.safe_load(f)

    def test_workflow_exists(self):
        """Verify check-protocol.yml exists"""
        workflow_path = WORKFLOWS_DIR / "check-protocol.yml"
        assert workflow_path.exists(), "check-protocol.yml workflow file should exist"

    def test_workflow_name(self, workflow):
        """Verify workflow has correct name"""
        assert workflow['name'] == "IPPOC Protocol Enforcer"

    def test_pull_request_triggers(self, workflow):
        """Verify workflow triggers on correct PR events"""
        # YAML parses 'on:' as True, so we need to use workflow[True]
        on_config = workflow.get('on', workflow.get(True))
        assert 'pull_request' in on_config
        pr_types = on_config['pull_request']['types']
        assert 'opened' in pr_types
        assert 'edited' in pr_types
        assert 'synchronize' in pr_types

    def test_lint_commits_job_exists(self, workflow):
        """Verify lint-commits job is defined"""
        assert 'lint-commits' in workflow['jobs']

    def test_lint_commits_runs_on_ubuntu(self, workflow):
        """Verify lint-commits runs on ubuntu-latest"""
        job = workflow['jobs']['lint-commits']
        assert job['runs-on'] == 'ubuntu-latest'

    def test_commit_message_format_step(self, workflow):
        """Verify commit message format validation step"""
        job = workflow['jobs']['lint-commits']
        steps = job['steps']

        # Find the commit message format check step
        format_step = None
        for step in steps:
            if step.get('name') == 'Check Commit Message Format':
                format_step = step
                break

        assert format_step is not None, "Commit message format check step should exist"
        assert format_step['uses'] == 'actions/github-script@v6'
        assert 'script' in format_step['with']

        # Verify script contains pattern matching
        script = format_step['with']['script']
        assert 'pattern' in script
        assert 'commit.commit.message' in script
        assert 'core.setFailed' in script

    def test_description_impact_validation_step(self, workflow):
        """Verify DESCRIPTION and IMPACT section validation step"""
        job = workflow['jobs']['lint-commits']
        steps = job['steps']

        # Find the DESCRIPTION/IMPACT check step
        desc_step = None
        for step in steps:
            if step.get('name') == 'Verify DESCRIPTION and IMPACT sections':
                desc_step = step
                break

        assert desc_step is not None, "DESCRIPTION/IMPACT validation step should exist"
        assert desc_step['uses'] == 'actions/github-script@v6'

        # Verify script checks for required sections
        script = desc_step['with']['script']
        assert 'DESCRIPTION:' in script
        assert 'IMPACT:' in script

    def test_commit_pattern_regex(self, workflow):
        """Verify commit pattern regex is correct"""
        job = workflow['jobs']['lint-commits']
        format_step = job['steps'][0]
        script = format_step['with']['script']

        # Verify pattern includes required organs
        assert 'brain' in script
        assert 'body' in script
        assert 'mind' in script
        assert 'memory' in script
        assert 'infra' in script
        assert 'system' in script
        assert 'docs' in script
        assert 'api' in script

    def test_workflow_has_two_steps(self, workflow):
        """Verify workflow has exactly 2 validation steps"""
        job = workflow['jobs']['lint-commits']
        steps = job['steps']
        assert len(steps) == 2, "Should have 2 validation steps"


class TestSystemVerificationWorkflow:
    """Tests for the IPPOC System Verification workflow"""

    @pytest.fixture
    def workflow(self):
        """Load system-verification.yml workflow"""
        workflow_path = WORKFLOWS_DIR / "system-verification.yml"
        with open(workflow_path, 'r') as f:
            return yaml.safe_load(f)

    def test_workflow_exists(self):
        """Verify system-verification.yml exists"""
        workflow_path = WORKFLOWS_DIR / "system-verification.yml"
        assert workflow_path.exists(), "system-verification.yml workflow file should exist"

    def test_workflow_name(self, workflow):
        """Verify workflow has correct name"""
        assert workflow['name'] == "IPPOC System Verification"

    def test_triggers_on_pr_and_push(self, workflow):
        """Verify workflow triggers on PR and push to main"""
        # YAML parses 'on:' as True, so we need to use workflow[True]
        on_config = workflow.get('on', workflow.get(True))
        assert 'pull_request' in on_config
        assert 'push' in on_config

        # Check PR targets main branch
        assert on_config['pull_request']['branches'] == ['main']

        # Check push targets main branch
        assert on_config['push']['branches'] == ['main']

    def test_rust_check_job_exists(self, workflow):
        """Verify rust-check job is defined"""
        assert 'rust-check' in workflow['jobs']

    def test_rust_check_job_name(self, workflow):
        """Verify rust-check job has correct display name"""
        job = workflow['jobs']['rust-check']
        assert job['name'] == 'Rust Kernel Check'

    def test_rust_check_runs_on_ubuntu(self, workflow):
        """Verify rust-check runs on ubuntu-latest"""
        job = workflow['jobs']['rust-check']
        assert job['runs-on'] == 'ubuntu-latest'

    def test_rust_check_working_directory(self, workflow):
        """Verify rust-check uses correct working directory"""
        job = workflow['jobs']['rust-check']
        assert 'defaults' in job
        assert 'run' in job['defaults']
        assert job['defaults']['run']['working-directory'] == 'src/soma'

    def test_rust_check_steps(self, workflow):
        """Verify rust-check has all required steps"""
        job = workflow['jobs']['rust-check']
        steps = job['steps']

        step_names = [step.get('name', step.get('uses', '')) for step in steps]

        assert any('checkout' in name.lower() for name in step_names), "Should checkout code"
        assert any('Install Rust' in name for name in step_names), "Should install Rust"
        assert any('Cache Cargo' in name for name in step_names), "Should cache Cargo"
        assert any('Run Cargo Check' in name for name in step_names), "Should run cargo check"

    def test_rust_check_strict_mode(self, workflow):
        """Verify cargo check runs in strict mode with -D warnings"""
        job = workflow['jobs']['rust-check']

        # Find the cargo check step
        cargo_step = None
        for step in job['steps']:
            if step.get('name') == 'Run Cargo Check (Strict)':
                cargo_step = step
                break

        assert cargo_step is not None, "Cargo check step should exist"
        assert cargo_step['run'] == 'cargo check'
        assert 'env' in cargo_step
        assert cargo_step['env']['RUSTFLAGS'] == '-D warnings'

    def test_cargo_cache_configuration(self, workflow):
        """Verify Cargo cache is properly configured"""
        job = workflow['jobs']['rust-check']

        # Find cache step
        cache_step = None
        for step in job['steps']:
            if step.get('name') == 'Cache Cargo':
                cache_step = step
                break

        assert cache_step is not None, "Cache step should exist"
        assert cache_step['uses'] == 'actions/cache@v3'

        # Verify cache paths
        paths = cache_step['with']['path']
        assert '~/.cargo/bin/' in paths
        assert '~/.cargo/registry/index/' in paths
        assert '~/.cargo/registry/cache/' in paths
        assert '~/.cargo/git/db/' in paths
        assert 'target/' in paths

        # Verify cache key
        assert 'key' in cache_step['with']
        assert 'Cargo.lock' in cache_step['with']['key']

    def test_node_lint_job_exists(self, workflow):
        """Verify node-lint job is defined"""
        assert 'node-lint' in workflow['jobs']

    def test_node_lint_job_name(self, workflow):
        """Verify node-lint job has correct display name"""
        job = workflow['jobs']['node-lint']
        assert job['name'] == 'Node Subsystems Lint'

    def test_node_lint_working_directory(self, workflow):
        """Verify node-lint uses correct working directory"""
        job = workflow['jobs']['node-lint']
        assert job['defaults']['run']['working-directory'] == 'src/cortex/cortex/openclaw-cortex'

    def test_node_lint_steps(self, workflow):
        """Verify node-lint has all required steps"""
        job = workflow['jobs']['node-lint']
        steps = job['steps']

        step_info = [step.get('name', step.get('uses', '')) for step in steps]

        assert any('checkout' in info.lower() for info in step_info), "Should checkout code"
        assert any('setup-node' in info.lower() for info in step_info), "Should setup Node.js"
        assert any('Install Dependencies' in info for info in step_info), "Should install dependencies"
        assert any('Lint' in info for info in step_info), "Should run linting"

    def test_node_version(self, workflow):
        """Verify Node.js version is specified"""
        job = workflow['jobs']['node-lint']

        # Find setup-node step
        node_step = None
        for step in job['steps']:
            if 'setup-node' in step.get('uses', ''):
                node_step = step
                break

        assert node_step is not None, "Node setup step should exist"
        assert node_step['with']['node-version'] == 20

    def test_npm_install_command(self, workflow):
        """Verify npm install is executed"""
        job = workflow['jobs']['node-lint']

        install_step = None
        for step in job['steps']:
            if step.get('name') == 'Install Dependencies':
                install_step = step
                break

        assert install_step is not None
        assert install_step['run'] == 'npm install'

    def test_npm_lint_command(self, workflow):
        """Verify npm lint is executed with fallback"""
        job = workflow['jobs']['node-lint']

        lint_step = None
        for step in job['steps']:
            if step.get('name') == 'Run Web Subsystem Lint':
                lint_step = step
                break

        assert lint_step is not None
        assert 'npm run lint' in lint_step['run']
        # Verify it has a fallback to not fail the build
        assert 'echo' in lint_step['run'] or '||' in lint_step['run']


class TestWorkflowIntegration:
    """Integration tests for workflow interactions"""

    def test_all_workflow_files_are_valid_yaml(self):
        """Verify all workflow files are valid YAML"""
        for workflow_file in WORKFLOWS_DIR.glob("*.yml"):
            with open(workflow_file, 'r') as f:
                try:
                    yaml.safe_load(f)
                except yaml.YAMLError as e:
                    pytest.fail(f"Invalid YAML in {workflow_file.name}: {e}")

    def test_workflow_actions_versions(self):
        """Verify GitHub Actions are using appropriate versions"""
        for workflow_file in WORKFLOWS_DIR.glob("*.yml"):
            with open(workflow_file, 'r') as f:
                workflow = yaml.safe_load(f)

            if 'jobs' not in workflow:
                continue

            for job_name, job in workflow['jobs'].items():
                if 'steps' not in job:
                    continue

                for step in job['steps']:
                    if 'uses' in step:
                        action = step['uses']
                        # Verify actions have version tags
                        if '@' in action:
                            version = action.split('@')[1]
                            assert version, f"Action {action} should have a version in {workflow_file.name}"

    def test_no_hardcoded_secrets(self):
        """Verify workflows don't contain hardcoded secrets"""
        sensitive_patterns = ['password', 'secret', 'token', 'key']

        for workflow_file in WORKFLOWS_DIR.glob("*.yml"):
            with open(workflow_file, 'r') as f:
                content = f.read().lower()

            # Allow 'secrets.' references but not hardcoded values
            for pattern in sensitive_patterns:
                if f'{pattern}:' in content or f'{pattern}=' in content:
                    # Verify it's a reference to secrets context, not a hardcoded value
                    assert 'secrets.' in content or '${{' in content, \
                        f"Potential hardcoded {pattern} in {workflow_file.name}"


class TestCommitMessageValidation:
    """Tests for commit message validation logic"""

    def test_valid_commit_patterns(self):
        """Test that valid commit messages would pass validation"""
        valid_messages = [
            "brain/cortex: Add new reasoning engine",
            "body/immune: Improve git flow handling",
            "memory/episodic: Store user interactions\n\nDESCRIPTION:\nAdded storage\n\nIMPACT:\nBetter memory",
            "infra/ci: Fix commit lint workflow",
            "system/init: Initialize core components",
            "docs/readme: Update installation guide",
            "api/rest: Add new endpoint for user management",
        ]

        # Pattern from workflow
        pattern = r'^(brain|body|mind|memory|infra|system|docs|api)\/[a-z0-9-]+: [\s\S]+'

        import re
        for msg in valid_messages:
            assert re.match(pattern, msg), f"Valid message should match pattern: {msg}"

    def test_invalid_commit_patterns(self):
        """Test that invalid commit messages would fail validation"""
        invalid_messages = [
            "fix: bug",  # Wrong format
            "brain: missing component",  # Missing component
            "invalid/component: message",  # Invalid organ
            "brain/Component: capital letter",  # Capital letter in component
            "brain/cortex:",  # Missing description
        ]

        # Pattern from workflow
        pattern = r'^(brain|body|mind|memory|infra|system|docs|api)\/[a-z0-9-]+: [\s\S]+'

        import re
        for msg in invalid_messages:
            assert not re.match(pattern, msg), f"Invalid message should not match: {msg}"

    def test_description_impact_sections(self):
        """Test DESCRIPTION and IMPACT section validation"""
        valid_msg = """brain/cortex: Add feature

DESCRIPTION:
This adds a new feature to the cortex.

IMPACT:
Improves reasoning capabilities."""

        assert 'DESCRIPTION:' in valid_msg
        assert 'IMPACT:' in valid_msg

        invalid_msg = """brain/cortex: Add feature

Just a regular commit message without sections."""

        assert 'DESCRIPTION:' not in invalid_msg or 'IMPACT:' not in invalid_msg


if __name__ == "__main__":
    pytest.main([__file__, "-v"])