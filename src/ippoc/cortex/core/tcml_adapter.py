"""
Brain Integration for Temporal-Causal Memory Layer
Exposes WHY() and WHAT_CHANGED() capabilities to the reasoning engine.
"""

from typing import Dict, Any, List, Optional
from memory.logic.tcml import TCMLState, NodeType
from memory.logic.causal_tracker import get_causal_tracker
import json

class TCMLBrainAdapter:
    """Adapter exposing TCML capabilities to Brain reasoning"""
    
    def __init__(self):
        self.tcml_state = TCMLState()
        self.tracker = get_causal_tracker(self.tcml_state)
    
    def why(self, outcome_node_id: str) -> Dict[str, Any]:
        """
        Answer "Why did this happen?"
        Returns causal chain analysis for any outcome.
        """
        return self.tcml_state.why(outcome_node_id)
    
    def what_changed(self, period_start: float, period_end: float) -> Dict[str, Any]:
        """
        Answer "What changed between these times?"
        Analyzes behavioral shifts and significant events.
        """
        return self.tcml_state.what_changed(period_start, period_end)
    
    def start_reasoning_session(self, task_description: str, context: Dict[str, Any]) -> str:
        """
        Begin tracking a reasoning/decision session.
        Returns session ID for later correlation.
        """
        session_id = f"session_{hash(task_description + str(context)) % 1000000}"
        self.tracker.start_decision_session(session_id, {
            "task": task_description,
            "context": context,
            "source": "brain_reasoning"
        })
        return session_id
    
    def record_tool_use(self, session_id: str, tool_name: str, 
                       input_params: Dict[str, Any], result: Dict[str, Any],
                       cost: float, success: bool) -> None:
        """
        Record tool execution during reasoning.
        Builds causal chain automatically.
        """
        self.tracker.record_tool_execution(
            session_id=session_id,
            tool_name=tool_name,
            input_data=input_params,
            result=result,
            cost=cost,
            success=success
        )
    
    def record_decision_outcome(self, session_id: str, outcome: str, 
                               success: bool, metrics: Optional[Dict[str, Any]] = None) -> None:
        """
        Record final outcome of reasoning session.
        Completes causal chain and enables analysis.
        """
        self.tracker.record_outcome(
            session_id=session_id,
            outcome_desc=outcome,
            success=success,
            metrics=metrics
        )
    
    def get_session_analysis(self, session_id: str) -> Dict[str, Any]:
        """
        Get complete causal analysis of a reasoning session.
        """
        return self.tracker.get_session_insight(session_id)
    
    def find_failure_patterns(self) -> List[Dict[str, Any]]:
        """
        Identify systemic failure patterns across all sessions.
        """
        return self.tracker.find_failure_patterns()
    
    def record_external_influence(self, event_description: str, source: str) -> None:
        """
        Record external events that might influence reasoning.
        """
        self.tracker.record_external_event(event_description, source)
    
    def get_recent_decisions(self, hours_back: int = 24) -> List[Dict[str, Any]]:
        """
        Get recent decision history with outcomes.
        """
        cutoff_time = self.tcml_state.nodes[-1].timestamp - (hours_back * 3600) if self.tcml_state.nodes else 0
        recent_nodes = [n for n in self.tcml_state.nodes 
                       if n.timestamp > cutoff_time and n.node_type in [NodeType.DECISION, NodeType.OUTCOME]]
        
        decisions = []
        for node in recent_nodes:
            if node.node_type == NodeType.DECISION:
                # Find corresponding outcome
                outcome = None
                for edge_id in node.effects:
                    if edge_id in self.tcml_state.node_index:
                        effect_node = self.tcml_state.nodes[self.tcml_state.node_index[edge_id]]
                        if effect_node.node_type == NodeType.OUTCOME:
                            outcome = effect_node
                            break
                
                decisions.append({
                    "decision_id": node.id,
                    "content": node.content,
                    "timestamp": node.timestamp,
                    "outcome": outcome.content if outcome else None,
                    "success": outcome.metadata.get("success") if outcome else None,
                    "regret": outcome.regret_level if outcome else None
                })
        
        return sorted(decisions, key=lambda d: d["timestamp"], reverse=True)
    
    def export_memory_graph(self) -> Dict[str, Any]:
        """
        Export complete memory graph for visualization/debugging.
        """
        return {
            "nodes": [
                {
                    "id": node.id,
                    "type": node.node_type.value,
                    "content": node.content,
                    "timestamp": node.timestamp,
                    "confidence": node.confidence,
                    "regret": node.regret_level,
                    "causes": node.causes,
                    "effects": node.effects
                }
                for node in self.tcml_state.nodes
            ],
            "edges": [
                {
                    "id": edge.id,
                    "from": edge.from_node,
                    "to": edge.to_node,
                    "confidence": edge.confidence,
                    "latency_ms": edge.latency_ms
                }
                for edge in self.tcml_state.edges
            ]
        }
    
    def import_memory_graph(self, data: Dict[str, Any]) -> None:
        """
        Import memory graph from exported data.
        """
        # Clear existing state
        self.tcml_state = TCMLState()
        self.tracker = get_causal_tracker(self.tcml_state)
        
        # Import nodes
        for node_data in data.get("nodes", []):
            node = self.tcml_state.nodes[-1] if self.tcml_state.nodes else None  # Placeholder
            # Actual reconstruction would require proper deserialization
            
        # Import edges  
        for edge_data in data.get("edges", []):
            edge = self.tcml_state.edges[-1] if self.tcml_state.edges else None  # Placeholder
            # Actual reconstruction would require proper deserialization

# Global adapter instance
_tcml_adapter: Optional[TCMLBrainAdapter] = None

def get_tcml_adapter() -> TCMLBrainAdapter:
    """Get singleton TCML adapter instance"""
    global _tcml_adapter
    if _tcml_adapter is None:
        _tcml_adapter = TCMLBrainAdapter()
    return _tcml_adapter

def reset_tcml_adapter() -> None:
    """Reset adapter (for testing)"""
    global _tcml_adapter
    _tcml_adapter = None

# Convenience functions for direct access
def WHY(outcome_node_id: str) -> Dict[str, Any]:
    """Convenience function for causal analysis"""
    return get_tcml_adapter().why(outcome_node_id)

def WHAT_CHANGED(period_start: float, period_end: float) -> Dict[str, Any]:
    """Convenience function for temporal analysis"""
    return get_tcml_adapter().what_changed(period_start, period_end)

def START_REASONING_SESSION(task_description: str, context: Dict[str, Any]) -> str:
    """Convenience function to start tracking reasoning session"""
    return get_tcml_adapter().start_reasoning_session(task_description, context)