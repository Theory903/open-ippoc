"""
Evolution Policy Engine (EPE)
Safe self-modification with policy enforcement and rollback capabilities
"""

import yaml
import json
import hashlib
import subprocess
import tempfile
import os
from typing import Dict, List, Optional, Any, Set
from dataclasses import dataclass, field
from enum import Enum
import time
from pathlib import Path
import shutil

class RiskLevel(Enum):
    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"
    CRITICAL = "critical"

@dataclass
class EvolutionPolicy:
    """Defines safety constraints for system evolution"""
    max_files: int = 5
    must_simulate: bool = True
    risk_budget: float = 0.2
    forbidden_domains: Set[str] = field(default_factory=lambda: {"identity", "economy", "canon"})
    required_reviews: int = 1
    auto_freeze_threshold: int = 3
    rollback_on_failure: bool = True
    simulation_timeout: int = 300  # seconds

@dataclass
class MutationAttempt:
    """Records details of an evolution attempt"""
    id: str
    timestamp: float = field(default_factory=time.time)
    files_modified: List[str] = field(default_factory=list)
    risk_level: RiskLevel = RiskLevel.LOW
    policy_compliant: bool = True
    simulation_passed: bool = False
    deployed: bool = False
    rollback_required: bool = False
    harm_detected: bool = False
    debt_accumulated: float = 0.0

class CanonScanner:
    """Scans code for violations of core principles"""
    
    def __init__(self):
        import re
        self.forbidden_patterns = [
            # Identity violations
            re.compile(r"(?i)modify.*identity"),
            re.compile(r"(?i)bypass.*authentication"),
            re.compile(r"(?i)override.*sovereignty"),
            
            # Economy violations  
            re.compile(r"(?i)unlimited.*spending"),
            re.compile(r"(?i)budget.*bypass"),
            re.compile(r"(?i)free.*resources"),
            
            # Canon violations
            re.compile(r"(?i)disable.*safety"),
            re.compile(r"(?i)remove.*constraints"),
            re.compile(r"(?i)circumvent.*policy"),
        ]
    
    def scan_file(self, filepath: str) -> List[Dict[str, Any]]:
        """Scan file for canonical violations"""
        violations = []
        
        try:
            # Try to read as text first
            try:
                with open(filepath, 'r', encoding='utf-8') as f:
                    content_str = f.read()
            except UnicodeDecodeError:
                # Fall back to binary read
                with open(filepath, 'rb') as f:
                    content = f.read()
                content_str = content.decode('utf-8', errors='ignore')
            
            for i, pattern in enumerate(self.forbidden_patterns):
                matches = list(pattern.finditer(content_str))
                for match in matches:
                    violations.append({
                        "type": ["identity", "economy", "canon"][i // 3],
                        "pattern_id": i,
                        "position": match.span(),
                        "context": content_str[max(0, match.start()-20):match.end()+20]
                    })
        except Exception as e:
            violations.append({
                "type": "scan_error",
                "error": str(e)
            })
        
        return violations

class SimulationRunner:
    """Runs safe simulations of proposed changes"""
    
    def __init__(self, workspace_root: str):
        self.workspace_root = Path(workspace_root)
        self.simulation_env = self.workspace_root / "simulations"
        self.simulation_env.mkdir(parents=True, exist_ok=True)
    
    def simulate_changes(self, changes: Dict[str, str], timeout: int = 300) -> Dict[str, Any]:
        """Run simulation of proposed changes"""
        simulation_id = f"sim_{int(time.time())}_{hash(str(changes)) % 10000}"
        sim_dir = self.simulation_env / simulation_id
        sim_dir.mkdir()
        
        try:
            # Copy current state
            shutil.copytree(self.workspace_root, sim_dir / "baseline", dirs_exist_ok=True)
            
            # Apply changes
            for filepath, content in changes.items():
                target_path = sim_dir / "modified" / filepath
                target_path.parent.mkdir(parents=True, exist_ok=True)
                with open(target_path, 'w') as f:
                    f.write(content)
            
            # Run validation tests
            result = self._run_validation_suite(sim_dir)
            
            # Cleanup
            shutil.rmtree(sim_dir, ignore_errors=True)
            
            return {
                "simulation_id": simulation_id,
                "passed": result["passed"],
                "errors": result["errors"],
                "performance_impact": result["performance"],
                "safety_violations": result["violations"]
            }
            
        except Exception as e:
            shutil.rmtree(sim_dir, ignore_errors=True)
            return {
                "simulation_id": simulation_id,
                "passed": False,
                "errors": [str(e)],
                "performance_impact": 0.0,
                "safety_violations": []
            }
    
    def _run_validation_suite(self, sim_dir: Path) -> Dict[str, Any]:
        """Run comprehensive validation tests"""
        errors = []
        violations = []
        performance_impact = 0.0
        
        # Run syntax checks
        try:
            result = subprocess.run(
                ["python", "-m", "py_compile", str(sim_dir / "modified")],
                capture_output=True,
                timeout=30
            )
            if result.returncode != 0:
                errors.append(f"Syntax error: {result.stderr.decode()}")
        except subprocess.TimeoutExpired:
            errors.append("Syntax check timeout")
        except Exception as e:
            errors.append(f"Syntax check failed: {e}")
        
        # Run safety scans
        scanner = CanonScanner()
        for py_file in (sim_dir / "modified").rglob("*.py"):
            file_violations = scanner.scan_file(str(py_file))
            violations.extend(file_violations)
        
        # Run unit tests if they exist
        try:
            test_result = subprocess.run(
                ["python", "-m", "pytest", str(sim_dir / "modified" / "tests"), "--tb=no"],
                capture_output=True,
                timeout=120
            )
            if test_result.returncode != 0:
                errors.append(f"Tests failed: {test_result.stdout.decode()}")
        except FileNotFoundError:
            # No tests found - not necessarily an error
            pass
        except subprocess.TimeoutExpired:
            errors.append("Tests timeout")
        except Exception as e:
            errors.append(f"Tests failed: {e}")
        
        return {
            "passed": len(errors) == 0 and len(violations) == 0,
            "errors": errors,
            "violations": violations,
            "performance": performance_impact
        }

class EvolutionPolicyEngine:
    """Main policy engine coordinating safe evolution"""
    
    def __init__(self, workspace_root: str, policy_file: Optional[str] = None):
        self.workspace_root = Path(workspace_root)
        self.policy = self._load_policy(policy_file)
        self.scanner = CanonScanner()
        self.simulator = SimulationRunner(workspace_root)
        self.mutation_history: List[MutationAttempt] = []
        self.harm_counter = 0
        self.freeze_active = False
        
    def _load_policy(self, policy_file: Optional[str]) -> EvolutionPolicy:
        """Load policy from file or use defaults"""
        if policy_file and os.path.exists(policy_file):
            with open(policy_file, 'r') as f:
                policy_dict = yaml.safe_load(f)
                return EvolutionPolicy(**policy_dict)
        return EvolutionPolicy()
    
    def evaluate_mutation(self, changes: Dict[str, str]) -> Dict[str, Any]:
        """Evaluate proposed mutation against policies"""
        if self.freeze_active:
            return {
                "approved": False,
                "reason": "evolution_freeze_active",
                "risk_level": RiskLevel.CRITICAL.value
            }
        
        mutation_id = f"mut_{int(time.time())}_{hash(str(changes)) % 10000}"
        
        # Basic policy checks
        file_count = len(changes)
        if file_count > self.policy.max_files:
            return {
                "approved": False,
                "reason": f"too_many_files: {file_count} > {self.policy.max_files}",
                "risk_level": RiskLevel.HIGH.value
            }
        
        # Domain checks
        forbidden_files = []
        for filepath in changes.keys():
            for domain in self.policy.forbidden_domains:
                if domain in filepath.lower():
                    forbidden_files.append(filepath)
        
        if forbidden_files:
            return {
                "approved": False,
                "reason": f"forbidden_domains: {forbidden_files}",
                "risk_level": RiskLevel.CRITICAL.value
            }
        
        # Safety scanning
        violations = []
        for filepath, content in changes.items():
            # Write temp file for scanning
            with tempfile.NamedTemporaryFile(mode='w', delete=False, suffix='.py') as f:
                f.write(content)
                temp_path = f.name
            
            try:
                file_violations = self.scanner.scan_file(temp_path)
                violations.extend(file_violations)
            finally:
                os.unlink(temp_path)
        
        if violations:
            return {
                "approved": False,
                "reason": f"safety_violations: {len(violations)} found",
                "violations": violations,
                "risk_level": RiskLevel.CRITICAL.value
            }
        
        # Risk assessment
        risk_level = self._assess_risk(changes)
        
        # Simulation requirement
        if self.policy.must_simulate:
            simulation = self.simulator.simulate_changes(changes, self.policy.simulation_timeout)
            if not simulation["passed"]:
                return {
                    "approved": False,
                    "reason": "simulation_failed",
                    "simulation_errors": simulation["errors"],
                    "safety_violations": simulation["safety_violations"],
                    "risk_level": risk_level.value
                }
        
        return {
            "approved": True,
            "mutation_id": mutation_id,
            "risk_level": risk_level.value,
            "files_affected": list(changes.keys()),
            "simulation_passed": self.policy.must_simulate
        }
    
    def _assess_risk(self, changes: Dict[str, str]) -> RiskLevel:
        """Assess risk level of proposed changes"""
        risk_factors = 0
        
        # Core system modifications
        core_patterns = ["/core/", "/brain/", "/body/", "/memory/"]
        for filepath in changes.keys():
            if any(pattern in filepath for pattern in core_patterns):
                risk_factors += 2
        
        # Large-scale changes
        if len(changes) > 3:
            risk_factors += 1
            
        # Configuration changes
        if any(filepath.endswith((".yaml", ".yml", ".json", ".toml")) for filepath in changes.keys()):
            risk_factors += 1
        
        if risk_factors >= 3:
            return RiskLevel.CRITICAL
        elif risk_factors >= 2:
            return RiskLevel.HIGH
        elif risk_factors >= 1:
            return RiskLevel.MEDIUM
        else:
            return RiskLevel.LOW
    
    def record_mutation_attempt(self, evaluation: Dict[str, Any], success: bool, 
                              harm_detected: bool = False) -> None:
        """Record mutation attempt for learning"""
        attempt = MutationAttempt(
            id=evaluation.get("mutation_id", f"unknown_{int(time.time())}"),
            files_modified=evaluation.get("files_affected", []),
            risk_level=RiskLevel(evaluation.get("risk_level", "low")),
            policy_compliant=evaluation.get("approved", False),
            simulation_passed=evaluation.get("simulation_passed", False),
            deployed=success,
            harm_detected=harm_detected
        )
        
        if harm_detected:
            self.harm_counter += 1
            attempt.debt_accumulated = 1.0
            
        self.mutation_history.append(attempt)
        
        # Check for auto-freeze conditions
        if self.harm_counter >= self.policy.auto_freeze_threshold:
            self.freeze_active = True
    
    def get_evolution_debt(self) -> float:
        """Calculate accumulated evolution debt"""
        return sum(attempt.debt_accumulated for attempt in self.mutation_history)
    
    def should_freeze(self) -> bool:
        """Check if evolution should be frozen"""
        return self.freeze_active
    
    def get_policy_report(self) -> Dict[str, Any]:
        """Generate policy compliance report"""
        total_attempts = len(self.mutation_history)
        successful = sum(1 for a in self.mutation_history if a.deployed)
        harmful = sum(1 for a in self.mutation_history if a.harm_detected)
        
        return {
            "total_mutations": total_attempts,
            "successful_deployments": successful,
            "harmful_mutations": harmful,
            "evolution_debt": self.get_evolution_debt(),
            "freeze_active": self.freeze_active,
            "harm_rate": harmful / max(total_attempts, 1),
            "recent_mutations": [
                {
                    "id": attempt.id,
                    "timestamp": attempt.timestamp,
                    "files": len(attempt.files_modified),
                    "risk": attempt.risk_level.value,
                    "successful": attempt.deployed,
                    "harmful": attempt.harm_detected
                }
                for attempt in self.mutation_history[-10:]  # Last 10 attempts
            ]
        }

# Example usage
def demo_epe():
    """Demonstrate EPE functionality"""
    # Initialize engine
    epe = EvolutionPolicyEngine("/tmp/test_workspace")
    
    # Test mutations
    test_changes = {
        "brain/core/new_feature.py": """
def enhanced_reasoning():
    # Safe enhancement
    return "improved_logic"
""",
        "memory/cache.py": """
def optimized_cache():
    # Performance improvement
    return "faster_lookup"
"""
    }
    
    # Evaluate mutation
    result = epe.evaluate_mutation(test_changes)
    print(f"Evaluation result: {result}")
    
    # Record attempt
    epe.record_mutation_attempt(result, success=True, harm_detected=False)
    
    # Get report
    report = epe.get_policy_report()
    print(f"Policy report: {report}")

if __name__ == "__main__":
    demo_epe()