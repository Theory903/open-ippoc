# brain/evolution/git_driver.py
# @cognitive - IPPOC Git Evolution Driver
# The Hands that rewrite the DNA.

import subprocess
import os
import time
from typing import Dict, Any, Optional

class GitDriver:
    """
    Safe wrapper for Git operations performed by the organism.
    Driven by the Evolver intent.
    """
    def __init__(self, repo_path: str = "."):
        self.repo_path = os.path.abspath(repo_path)

    def _run(self, args: list[str]) -> Dict[str, Any]:
        """Runs a git command in the repo path."""
        try:
            result = subprocess.run(
                ["git"] + args,
                cwd=self.repo_path,
                capture_output=True,
                text=True,
                check=False
            )
            return {
                "success": result.returncode == 0,
                "stdout": result.stdout.strip(),
                "stderr": result.stderr.strip(),
                "code": result.returncode
            }
        except Exception as e:
            return {"success": False, "error": str(e), "code": -1}

    def create_mutation_branch(self, mutation_id: str) -> Dict[str, Any]:
        """Creates and switches to a new mutation branch."""
        branch_name = f"ippoc/mutation/{mutation_id}"
        # Ensure we are clean first? Or just stash?
        # For v1, we assume we can branch off current state.
        
        # 1. Create branch
        res = self._run(["checkout", "-b", branch_name])
        if res["success"]:
            return {"success": True, "branch": branch_name}
        return res

    def commit_mutation(self, message: str) -> Dict[str, Any]:
        """STAGES ALL variations and commits them."""
        # 1. Add all
        self._run(["add", "."])
        
        # 2. Commit
        # Enforce commit format?
        if not message.startswith("feat(evolution):") and not message.startswith("fix(evolution):"):
             message = f"feat(evolution): {message}"
             
        res = self._run(["commit", "-m", message])
        return res

    def revert_mutation(self) -> Dict[str, Any]:
        """Hard resets the current branch to HEAD~1 or cleans up."""
        # Actually, if we are in a mutation branch, we might want to just switch back to main and delete the branch?
        # But 'revert' usually means undoing the last commit in the current flow.
        # Let's assume we want to undo the changes of the mutation but stay on branch?
        # Or better: discard changes if testing failed.
        return self._run(["reset", "--hard", "HEAD"])

    def checkout_main(self) -> Dict[str, Any]:
        return self._run(["checkout", "main"])

    def merge_mutation(self, branch_name: str) -> Dict[str, Any]:
        """Merges mutation into main (Squash merge usually better for evolution)."""
        # 1. Switch to main
        self.checkout_main()
        
        # 2. Merge --squash (Wait, we want history? Maybe no-ff?)
        # Let's use standard merge for now to preserve the mutation history node
        return self._run(["merge", "--no-ff", branch_name])

    def get_current_branch(self) -> str:
        res = self._run(["rev-parse", "--abbrev-ref", "HEAD"])
        return res.get("stdout", "unknown")
