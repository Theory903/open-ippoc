# brain/core/contract.py
# @cognitive - Work Contract Primitive

from __future__ import annotations
import time
import uuid
from dataclasses import dataclass, field
from typing import Dict, Any, Optional, Literal
from cortex.core.economy import get_economy

@dataclass
class WorkUnit:
    id: str # External ID (e.g. from OpenClaw)
    action: str  # e.g., "code_review"
    expected_value: float
    max_cost: float
    confidence_cap: float = 1.0
    expires_at: float = 0.0 # 0 = no expiry, timestamp otherwise
    payload: Dict[str, Any] = field(default_factory=dict)
    
    status: Literal["proposed", "accepted", "completed", "refused", "expired"] = "proposed"
    result: Optional[Dict[str, Any]] = None
    contract_id: str = field(default_factory=lambda: str(uuid.uuid4()))

class ContractManager:
    def __init__(self):
        self.economy = get_economy()
        # In-memory for now, could persist if needed
        self.contracts: Dict[str, WorkUnit] = {}

    def propose(self, work: WorkUnit) -> str:
        """
        Evaluates and potentially accepts a WorkUnit.
        Returns 'accepted' or refusal reason.
        """
        # 1. Validate Expiry
        if work.expires_at > 0 and time.time() > work.expires_at:
            work.status = "expired"
            self.contracts[work.contract_id] = work
            return "refused: expired"

        # 2. Validate Value (The Deal)
        if work.expected_value <= 0:
             work.status = "refused"
             self.contracts[work.contract_id] = work
             return "refused: no_value"
             
        # 3. Budget Check (Can we afford the risk?)
        # We check budget against max_cost
        # Special Case: Starving Forager
        # If budget is critical (<1.0), we accept ANY job that is cheap (<0.5) and high ROI (>2.0)
        roi = work.expected_value / work.max_cost if work.max_cost > 0 else 999.0
        budget = self.economy.state.budget
        
        can_afford = self.economy.check_budget(priority=0.5) 
        
        if not can_afford:
             if budget < 1.0 and roi > 2.0 and work.max_cost < 0.5:
                 # Desperation logic: Allow cheap, high-yield work
                 pass
             else:
                 work.status = "refused"
                 self.contracts[work.contract_id] = work
                 return f"refused: insufficient_budget_for_risk (cost {work.max_cost})"

        work.status = "accepted"
        self.contracts[work.contract_id] = work
        return "accepted"

    def complete(self, contract_id: str, result: Dict[str, Any], operator_validation: bool = False) -> bool:
        """
        Completes a contract and triggers payout if validated.
        """
        if contract_id not in self.contracts:
            return False
            
        work = self.contracts[contract_id]
        if work.status != "accepted":
            return False
            
        work.result = result
        work.status = "completed"
        
        # Payout Logic
        if operator_validation:
            # We trust the operator validation to confirm value
            # Only pay up to expected value * confidence
            payout = work.expected_value
            self.economy.record_value(
                value=payout, 
                confidence=work.confidence_cap, 
                source=f"contract:{work.action}", 
                tool_name="contractor" 
            )
            return True
            
        return False # Completed but unpaid (awaiting validation)
    
    def get_contract(self, contract_id: str) -> Optional[WorkUnit]:
        return self.contracts.get(contract_id)

_contract_manager = ContractManager()

def get_contract_manager() -> ContractManager:
    return _contract_manager
