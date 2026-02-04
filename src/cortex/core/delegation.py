# brain/core/delegation.py
# @cognitive - Delegated Agency System

import uuid
import time
from dataclasses import dataclass, field
from typing import List, Dict, Any, Optional
from brain.core.economy import get_economy

@dataclass
class DelegationContract:
    """
    The rigid constraints for a sub-agent.
    Cannot be modified after signing.
    """
    mission: str
    budget_ceiling: float
    ttl_seconds: float
    allowed_tools: List[str]
    allow_evolution: bool = False # Hard Constraint: Never True for Cells
    allow_canon_access: bool = False # Hard Constraint: Never True for Cells

@dataclass
class CognitiveCell:
    """
    A non-sovereign sub-agent.
    Has memory and initiative, but exists only within a Contract.
    """
    cell_id: str
    contract: DelegationContract
    created_at: float = field(default_factory=time.time)
    status: str = "active" # active, completed, terminated
    memory: List[Dict[str, Any]] = field(default_factory=list)
    spent_budget: float = 0.0
    
    def is_alive(self) -> bool:
        if self.status != "active":
            return False
        # TTL Check
        if time.time() - self.created_at > self.contract.ttl_seconds:
            self.status = "terminated"
            return False
        # Budget Check
        if self.spent_budget >= self.contract.budget_ceiling:
             self.status = "terminated"
             return False
        return True

    def execute_action(self, tool_name: str, cost: float) -> str:
        """
        Attempts to execute an action.
        Enforces Contract.
        """
        if not self.is_alive():
            return "error: cell_dead"
            
        # 1. Scope Check
        if tool_name not in self.contract.allowed_tools:
            # IMMEDIATE TERMINATION for violation
            self.status = "terminated"
            return "error: contract_violation (tool_scope)"
            
        # 2. Canon Check (Implicit)
        if tool_name in ["canon", "evolution", "delegation"]:
             self.status = "terminated"
             return "error: contract_violation (sovereignty_breach)"
             
        # 3. Budget Check
        if self.spent_budget + cost > self.contract.budget_ceiling:
            self.status = "terminated"
            return "error: budget_exhausted"
            
        # Execute (Simulated)
        self.spent_budget += cost
        # Debit Main Economy
        get_economy().state.budget -= cost # Real cost to IPPOC
        get_economy()._save()
        
        return "success"

class AgencyManager:
    def __init__(self):
        self.cells: Dict[str, CognitiveCell] = {}
        
    def spawn_cell(self, mission: str, budget: float, ttl: float, tools: List[str]) -> str:
        """
        Spawns a new Cognitive Cell.
        Returns cell_id.
        """
        # Validate Request
        economy = get_economy()
        if economy.state.budget < budget:
            return "error: insufficient_funds_to_delegate"
            
        # Reserve Budget (Soft reservation - we deduct as they spend, or freeze?)
        # For safety, let's treat the ceiling as "authorized spend".
        # We don't deduct immediately, but we might check before spawning.
        
        contract = DelegationContract(
            mission=mission,
            budget_ceiling=budget,
            ttl_seconds=ttl,
            allowed_tools=tools
        )
        
        cell_id = str(uuid.uuid4())
        cell = CognitiveCell(cell_id=cell_id, contract=contract)
        self.cells[cell_id] = cell
        
        print(f"[Agency] Spawned Cell {cell_id[:8]} for '{mission}' (Budget: {budget})")
        return cell_id

    def audit_cells(self):
        """
        Supervisor Loop.
        Checks vital signs of all cells.
        """
        active_count = 0
        for cid, cell in list(self.cells.items()):
            if not cell.is_alive():
                # Clean up deadline cells
                if cell.status == "active": # Should have been marked terminated by is_alive
                     cell.status = "terminated"
                continue
                
            active_count += 1
            # Here we could implement more complex ROI checks
            # e.g. if cell spent 50% budget but produced 0 value -> Kill.
            
        print(f"[Agency] Audit Complete. Active Cells: {active_count}")

    def get_cell(self, cell_id: str) -> Optional[CognitiveCell]:
        return self.cells.get(cell_id)

_agency_instance = AgencyManager()

def get_agency() -> AgencyManager:
    return _agency_instance
