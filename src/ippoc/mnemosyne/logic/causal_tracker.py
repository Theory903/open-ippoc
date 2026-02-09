"""
Causal Edge Writer for ToolOrchestrator integration
Tracks cause-effect relationships during tool execution and decision making.
"""

from typing import List, Dict, Any, Optional
from memory.logic.tcml import TCMLState, MemoryNode, CausalEdge, NodeType
from uuid import uuid4
import time

class CausalTracker:
    """Tracks causal relationships in tool execution and decision flows"""
    
    def __init__(self, tcml_state: TCMLState):
        self.tcml = tcml_state
        self.active_sessions: Dict[str, List[str]] = {}  # session_id -> [node_ids]
        self.pending_causes: Dict[str, List[str]] = {}   # node_id -> [cause_node_ids]
    
    def start_decision_session(self, session_id: str, context: Dict[str, Any]) -> str:
        """Start tracking a decision-making session"""
        node = MemoryNode(
            id=f"decision_{uuid4().hex[:12]}",
            node_type=NodeType.DECISION,
            content=f"Decision session started: {context.get('task', 'unknown')}",
            source=context.get('source', 'unknown'),
            metadata={
                "session_id": session_id,
                "context": context,
                "status": "started"
            }
        )
        
        self.tcml.add_node(node)
        self.active_sessions[session_id] = [node.id]
        return node.id
    
    def record_tool_execution(self, session_id: str, tool_name: str, 
                            input_data: Dict[str, Any], result: Dict[str, Any],
                            cost: float, success: bool) -> str:
        """Record a tool execution as an observation"""
        node = MemoryNode(
            id=f"tool_{uuid4().hex[:12]}",
            node_type=NodeType.OBSERVATION,
            content=f"Executed {tool_name}: {'SUCCESS' if success else 'FAILED'}",
            source="tool_orchestrator",
            confidence=0.9 if success else 0.7,
            metadata={
                "tool_name": tool_name,
                "input": input_data,
                "result": result,
                "cost": cost,
                "success": success,
                "session_id": session_id
            }
        )
        
        self.tcml.add_node(node)
        
        # Link to session if active
        if session_id in self.active_sessions:
            self.active_sessions[session_id].append(node.id)
            # Create pending cause relationship
            if session_id not in self.pending_causes:
                self.pending_causes[session_id] = []
            self.pending_causes[session_id].append(node.id)
        
        return node.id
    
    def record_outcome(self, session_id: str, outcome_desc: str, 
                      success: bool, metrics: Dict[str, Any] = None) -> str:
        """Record the outcome of a decision session"""
        node = MemoryNode(
            id=f"outcome_{uuid4().hex[:12]}",
            node_type=NodeType.OUTCOME,
            content=outcome_desc,
            source="evaluation",
            confidence=0.95,
            regret_level=0.0 if success else 0.8,  # High regret for failures
            metadata={
                "session_id": session_id,
                "success": success,
                "metrics": metrics or {},
                "evaluated_at": time.time()
            }
        )
        
        self.tcml.add_node(node)
        
        # Link to session and create causal edges
        if session_id in self.active_sessions:
            self.active_sessions[session_id].append(node.id)
            
            # Create causal edges from all session nodes to outcome
            for cause_node_id in self.active_sessions[session_id][:-1]:  # All except outcome itself
                edge = CausalEdge(
                    id=f"edge_{uuid4().hex[:12]}",
                    from_node=cause_node_id,
                    to_node=node.id,
                    confidence=0.8,  # Moderate confidence
                    context={"session_id": session_id}
                )
                self.tcml.add_edge(edge)
            
            # Clear session
            del self.active_sessions[session_id]
            if session_id in self.pending_causes:
                del self.pending_causes[session_id]
        
        return node.id
    
    def record_external_event(self, event_desc: str, source: str, 
                            timestamp: Optional[float] = None) -> str:
        """Record external events that might influence decisions"""
        node = MemoryNode(
            id=f"event_{uuid4().hex[:12]}",
            node_type=NodeType.EVENT,
            content=event_desc,
            source=source,
            timestamp=timestamp or time.time(),
            confidence=0.9
        )
        
        self.tcml.add_node(node)
        return node.id
    
    def get_session_insight(self, session_id: str) -> Dict[str, Any]:
        """Get causal analysis for a completed session"""
        if session_id in self.active_sessions:
            return {"status": "in_progress"}
        
        # Find the outcome node for this session
        outcome_nodes = [n for n in self.tcml.nodes 
                        if n.node_type == NodeType.OUTCOME 
                        and n.metadata.get("session_id") == session_id]
        
        if not outcome_nodes:
            return {"status": "not_found"}
        
        outcome_node = outcome_nodes[0]
        analysis = self.tcml.why(outcome_node.id)
        
        return {
            "status": "completed",
            "session_id": session_id,
            "outcome": outcome_node.content,
            "success": outcome_node.metadata.get("success", False),
            "regret_level": outcome_node.regret_level,
            "causal_analysis": analysis,
            "what_changed": self.tcml.what_changed(
                outcome_node.timestamp - 3600,  # Last hour
                outcome_node.timestamp
            )
        }
    
    def find_failure_patterns(self) -> List[Dict[str, Any]]:
        """Identify common failure patterns"""
        failures = [n for n in self.tcml.nodes 
                   if n.node_type == NodeType.OUTCOME 
                   and n.metadata.get("success") == False]
        
        patterns = []
        for failure in failures[-10:]:  # Last 10 failures
            causes = self.tcml.find_causes_of(failure.id)
            pattern = {
                "failure_id": failure.id,
                "failure_desc": failure.content,
                "timestamp": failure.timestamp,
                "direct_causes": [{"id": c.id, "content": c.content} for c in causes],
                "tools_involved": []
            }
            
            # Extract tools from causal chain
            for cause in causes:
                if "tool_name" in cause.metadata:
                    pattern["tools_involved"].append(cause.metadata["tool_name"])
            
            patterns.append(pattern)
        
        return patterns

# Global instance
_global_tracker: Optional[CausalTracker] = None

def get_causal_tracker(tcml_state: Optional[TCMLState] = None) -> CausalTracker:
    """Get or create global causal tracker"""
    global _global_tracker
    if _global_tracker is None:
        if tcml_state is None:
            tcml_state = TCMLState()
        _global_tracker = CausalTracker(tcml_state)
    elif tcml_state is not None:
        _global_tracker.tcml = tcml_state
    return _global_tracker

def reset_causal_tracker() -> None:
    """Reset the global tracker (for testing)"""
    global _global_tracker
    _global_tracker = None