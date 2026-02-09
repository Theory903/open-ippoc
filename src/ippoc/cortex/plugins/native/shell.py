import subprocess
import os
import sys
from typing import Dict, Any
from ippoc.cortex.core.tools.base import IPPOC_Tool, ToolInvocationEnvelope, ToolResult, CognitiveRole
from ippoc.cortex.core.exceptions import ToolExecutionError

class NativeShellAdapter(IPPOC_Tool):
    """
    A minimal, native Python shell actor for IPPOC.
    Provides basic filesystem and system introspection without external dependencies.
    """
    def __init__(self):
        super().__init__(name="native_shell", domain="system", role=CognitiveRole.ACTOR)
        # List of allowed commands for the native shell
        self.allowlist = {
            "ls", "pwd", "date", "cat", "grep", "find", 
            "ps", "top", "df", "du", "whoami", "uname"
        }

    def estimate_cost(self, envelope: ToolInvocationEnvelope) -> float:
        return 0.1

    async def execute(self, envelope: ToolInvocationEnvelope) -> ToolResult:
        action = envelope.action
        params = envelope.context.get("params", []) if isinstance(envelope.context.get("params"), list) else []
        cmd = envelope.context.get("command", action)

        if cmd not in self.allowlist:
             return ToolResult(
                success=False,
                output=f"Command '{cmd}' not in native allowlist.",
                error_code="forbidden_command"
            )

        # Safety Check: Path Traversal
        for p in params:
            ps = str(p)
            if ".." in ps or ps.startswith("/") or ps.startswith("~"):
                 return ToolResult(
                    success=False,
                    output=f"Security Violation: Dangerous parameter detected '{ps}'",
                    error_code="security_violation"
                )

        try:
            full_cmd = [cmd] + [str(p) for p in params]
            # Execute with timeout and restricted environment if needed
            result = subprocess.run(
                full_cmd, 
                capture_output=True, 
                text=True, 
                timeout=10,
                cwd=os.getenv("IPPOC_INSTANCE_DIR", ".")
            )
            
            return ToolResult(
                success=result.returncode == 0,
                output=result.stdout if result.returncode == 0 else result.stderr,
                cost_spent=0.1,
                warnings=[f"Exit code: {result.returncode}"] if result.returncode != 0 else []
            )
        except subprocess.TimeoutExpired:
            return ToolResult(
                success=False,
                output="Command timed out",
                error_code="timeout"
            )
        except Exception as e:
            return ToolResult(
                success=False,
                output=str(e),
                error_code="execution_failed"
            )
