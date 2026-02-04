# brain/gateway/ts_bridge.py
# @cognitive - Python ↔ TypeScript Bridge for IPPOC-OpenClaw Integration

import json
import subprocess
import asyncio
import logging
from typing import Dict, Any, Optional
from pathlib import Path

from cortex.core.exceptions import ToolExecutionError

logger = logging.getLogger("IPPOC.TSBridge")

class TypeScriptBridge:
    """
    Bridge between Python Cortex and TypeScript OpenClaw components.
    Leverages existing ippoc-adapter.ts for seamless integration.
    """
    
    def __init__(self, repo_root: str = "."):
        self.repo_root = Path(repo_root).resolve()
        self.adapter_path = self.repo_root / "src" / "cortex" / "cortex" / "openclaw-cortex" / "src" / "ippoc-adapter.ts"
        self.node_modules_path = self.repo_root / "src" / "kernel" / "openclaw" / "node_modules"
        self.initialized = False
        
    async def initialize(self) -> bool:
        """Initialize the TypeScript bridge"""
        if self.initialized:
            return True
            
        # Verify adapter exists
        if not self.adapter_path.exists():
            logger.error(f"IPPOC adapter not found at {self.adapter_path}")
            return False
            
        # Check if node_modules exists (TypeScript dependencies)
        if not self.node_modules_path.exists():
            logger.warning("Node modules not found - TypeScript components may not be available")
            # Try to build/install dependencies
            await self._install_dependencies()
            
        self.initialized = True
        logger.info("[TSBridge] TypeScript bridge initialized")
        return True
    
    async def _install_dependencies(self):
        """Install TypeScript dependencies if missing"""
        openclaw_root = self.repo_root / "src" / "kernel" / "openclaw"
        if openclaw_root.exists():
            try:
                logger.info("[TSBridge] Installing OpenClaw dependencies...")
                proc = await asyncio.create_subprocess_shell(
                    "pnpm install",
                    cwd=openclaw_root,
                    stdout=subprocess.PIPE,
                    stderr=subprocess.PIPE
                )
                stdout, stderr = await proc.communicate()
                if proc.returncode == 0:
                    logger.info("[TSBridge] Dependencies installed successfully")
                else:
                    logger.warning(f"[TSBridge] Dependency installation warning: {stderr.decode()}")
            except Exception as e:
                logger.error(f"[TSBridge] Failed to install dependencies: {e}")
    
    async def execute_ts_tool(self, tool_envelope: Dict[str, Any]) -> Dict[str, Any]:
        """
        Execute tool through TypeScript adapter.
        Bridges Python orchestrator calls to TypeScript OpenClaw tools.
        """
        if not await self.initialize():
            raise ToolExecutionError("ts_bridge", "Bridge initialization failed")
            
        try:
            # Convert envelope to TypeScript-compatible format
            ts_envelope = self._convert_to_ts_format(tool_envelope)
            
            # Execute via TypeScript adapter
            result = await self._call_ts_adapter(ts_envelope)
            
            # Convert result back to Python format
            py_result = self._convert_result_to_python(result)
            
            return py_result
            
        except Exception as e:
            logger.error(f"[TSBridge] TS tool execution failed: {e}")
            raise ToolExecutionError("ts_bridge", str(e))
    
    def _convert_to_ts_format(self, envelope: Dict[str, Any]) -> Dict[str, Any]:
        """Convert Python tool envelope to TypeScript format"""
        # Map Python domains to TypeScript equivalents
        domain_mapping = {
            "memory": "memory",
            "body": "body", 
            "evolution": "evolution",
            "cognition": "cognition",
            "economy": "economy",
            "social": "social",
            "simulation": "simulation"
        }
        
        ts_envelope = {
            "tool_name": envelope.get("tool_name", ""),
            "domain": domain_mapping.get(envelope.get("domain", ""), "cognition"),
            "action": envelope.get("action", ""),
            "context": envelope.get("context", {}),
            "risk_level": envelope.get("risk_level", "low"),
            "estimated_cost": envelope.get("estimated_cost", 0.0)
        }
        
        # Add optional fields if present
        if "requires_validation" in envelope:
            ts_envelope["requires_validation"] = envelope["requires_validation"]
        if "rollback_allowed" in envelope:
            ts_envelope["rollback_allowed"] = envelope["rollback_allowed"]
            
        return ts_envelope
    
    def _convert_result_to_python(self, ts_result: Dict[str, Any]) -> Dict[str, Any]:
        """Convert TypeScript result to Python format"""
        py_result = {
            "success": ts_result.get("success", False),
            "output": ts_result.get("output"),
            "cost_spent": ts_result.get("cost_spent", 0.0),
            "memory_written": ts_result.get("memory_written", False),
            "rollback_token": ts_result.get("rollback_token"),
            "warnings": ts_result.get("warnings", []),
            "error": ts_result.get("error")
        }
        return py_result
    
    async def _call_ts_adapter(self, envelope: Dict[str, Any]) -> Dict[str, Any]:
        """Call the TypeScript adapter with the tool envelope"""
        # Use node to execute the TypeScript adapter
        adapter_script = f"""
        const {{ getIPPOCAdapter }} = require('{self.adapter_path}');
        
        async function executeTool() {{
            const config = {{
                databaseUrl: "postgresql://localhost/ippoc",
                redisUrl: "redis://localhost:6379",
                orchestratorMode: "local",
                nodePort: 3000,
                nodeRole: "tool",
                enableEconomy: true,
                enableSelfEvolution: true,
                enableToolSmith: true,
                enableHardening: true,
                reputationThreshold: 0.7
            }};
            
            const adapter = getIPPOCAdapter(config);
            await adapter.initialize();
            
            const result = await adapter.invokeTool({json.dumps(envelope)});
            console.log(JSON.stringify(result));
        }}
        
        executeTool().catch(console.error);
        """
        
        try:
            # Write temporary script
            temp_script = self.repo_root / "temp_ts_executor.js"
            temp_script.write_text(adapter_script)
            
            # Execute with node
            proc = await asyncio.create_subprocess_exec(
                "node",
                str(temp_script),
                cwd=self.repo_root,
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE
            )
            
            stdout, stderr = await proc.communicate()
            
            # Clean up temp file
            temp_script.unlink(missing_ok=True)
            
            if proc.returncode != 0:
                error_msg = stderr.decode() if stderr else "Unknown error"
                raise Exception(f"TS adapter failed: {error_msg}")
                
            # Parse result
            result_str = stdout.decode().strip()
            if result_str:
                return json.loads(result_str)
            else:
                return {"success": False, "error": "Empty response from TS adapter"}
                
        except json.JSONDecodeError as e:
            raise Exception(f"Invalid JSON from TS adapter: {e}")
        except Exception as e:
            raise Exception(f"TS adapter execution failed: {e}")
    
    async def get_openclaw_skills(self) -> Dict[str, Any]:
        """Discover available OpenClaw skills through TS adapter"""
        try:
            # Query for available skills
            envelope = {
                "tool_name": "system",
                "domain": "cognition",
                "action": "list_skills",
                "context": {},
                "risk_level": "low",
                "estimated_cost": 0.1
            }
            
            result = await self.execute_ts_tool(envelope)
            if result["success"]:
                return result.get("output", {})
            else:
                logger.warning(f"[TSBridge] Failed to list skills: {result.get('error')}")
                return {}
                
        except Exception as e:
            logger.error(f"[TSBridge] Skill discovery failed: {e}")
            return {}
    
    def is_available(self) -> bool:
        """Check if TypeScript bridge is available"""
        return (
            self.adapter_path.exists() and 
            self.initialized
        )

# Global bridge instance
_ts_bridge: Optional[TypeScriptBridge] = None

def get_ts_bridge() -> TypeScriptBridge:
    global _ts_bridge
    if _ts_bridge is None:
        _ts_bridge = TypeScriptBridge()
    return _ts_bridge

async def initialize_bridge() -> bool:
    """Initialize the TypeScript bridge"""
    bridge = get_ts_bridge()
    return await bridge.initialize()