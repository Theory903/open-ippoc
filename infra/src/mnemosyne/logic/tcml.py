"""
Temporal-Causal Memory Layer (TCML)
Extends existing memory with time-aware causality tracking.

New primitives:
- MemoryNode: Events, decisions, observations with timestamps
- CausalEdge: Cause-effect relationships with confidence and latency
- Temporal queries: before/after, recurring patterns
"""

from typing import List, Dict, Any, Optional, Union
from pydantic import BaseModel, Field
from enum import Enum
import time
from datetime import datetime, timedelta
from dataclasses import dataclass

class NodeType(str, Enum):
    EVENT = "EVENT"           # Raw occurrence
    DECISION = "DECISION"     # Choice made
    OBSERVATION = "OBSERVATION"  # Perceived state
    OUTCOME = "OUTCOME"       # Result/consequence

class MemoryNode(BaseModel):
    """Enhanced memory node with temporal and causal awareness"""
    id: str
    node_type: NodeType
    timestamp: float = Field(default_factory=time.time)
    content: str
    source: str              # node_id/tool/peer
    confidence: float = 1.0
    metadata: Dict[str, Any] = Field(default_factory=dict)
    
    # Causal fields
    causes: List[str] = Field(default_factory=list)  # node IDs that caused this
    effects: List[str] = Field(default_factory=list)  # node IDs this caused
    regret_level: Optional[float] = None  # 0.0-1.0, how much we wish this didn't happen
    
    def __hash__(self):
        return hash(self.id)
    
    def time_since(self, other_timestamp: float) -> float:
        """Return seconds since another timestamp"""
        return self.timestamp - other_timestamp

class CausalEdge(BaseModel):
    """Represents a cause-effect relationship"""
    id: str
    from_node: str           # MemoryNode.id
    to_node: str             # MemoryNode.id
    confidence: float        # 0.0-1.0 strength of causal link
    latency_ms: Optional[int] = None  # Time between cause and effect
    context: Dict[str, Any] = Field(default_factory=dict)  # Conditions when this holds
    
    def __hash__(self):
        return hash(self.id)

@dataclass
class TemporalPattern:
    """Detected temporal pattern in memory"""
    pattern_type: str        # "daily", "weekly", "conditional", etc.
    nodes: List[str]         # MemoryNode IDs in pattern
    frequency: int           # How often observed
    confidence: float        # Pattern reliability
    description: str         # Human-readable summary

class TCMLState(BaseModel):
    """Extended memory state with temporal-causal capabilities"""
    # Extended from MemoryState
    nodes: List[MemoryNode] = Field(default_factory=list)
    edges: List[CausalEdge] = Field(default_factory=list)
    patterns: List[TemporalPattern] = Field(default_factory=list)
    
    # Indexes for fast querying
    node_index: Dict[str, int] = Field(default_factory=dict)  # id -> index in nodes list
    time_index: Dict[float, List[str]] = Field(default_factory=dict)  # timestamp -> node IDs
    type_index: Dict[NodeType, List[str]] = Field(default_factory=dict)  # type -> node IDs
    
    def add_node(self, node: MemoryNode) -> None:
        """Add a node and update indexes"""
        self.nodes.append(node)
        idx = len(self.nodes) - 1
        self.node_index[node.id] = idx
        
        # Update time index
        ts_key = node.timestamp
        if ts_key not in self.time_index:
            self.time_index[ts_key] = []
        self.time_index[ts_key].append(node.id)
        
        # Update type index
        if node.node_type not in self.type_index:
            self.type_index[node.node_type] = []
        self.type_index[node.node_type].append(node.id)
    
    def add_edge(self, edge: CausalEdge) -> None:
        """Add a causal edge"""
        self.edges.append(edge)
        
        # Update node references
        if edge.from_node in self.node_index:
            from_idx = self.node_index[edge.from_node]
            if edge.to_node not in self.nodes[from_idx].effects:
                self.nodes[from_idx].effects.append(edge.to_node)
        
        if edge.to_node in self.node_index:
            to_idx = self.node_index[edge.to_node]
            if edge.from_node not in self.nodes[to_idx].causes:
                self.nodes[to_idx].causes.append(edge.from_node)
    
    def find_before(self, timestamp: float, node_type: Optional[NodeType] = None) -> List[MemoryNode]:
        """Find all nodes that occurred before given timestamp"""
        result = []
        for node in self.nodes:
            if node.timestamp < timestamp:
                if node_type is None or node.node_type == node_type:
                    result.append(node)
        return sorted(result, key=lambda n: n.timestamp, reverse=True)
    
    def find_after(self, timestamp: float, node_type: Optional[NodeType] = None) -> List[MemoryNode]:
        """Find all nodes that occurred after given timestamp"""
        result = []
        for node in self.nodes:
            if node.timestamp > timestamp:
                if node_type is None or node.node_type == node_type:
                    result.append(node)
        return sorted(result, key=lambda n: n.timestamp)
    
    def find_causes_of(self, node_id: str) -> List[MemoryNode]:
        """Find all nodes that caused the given node"""
        if node_id not in self.node_index:
            return []
        
        node = self.nodes[self.node_index[node_id]]
        causes = []
        for cause_id in node.causes:
            if cause_id in self.node_index:
                causes.append(self.nodes[self.node_index[cause_id]])
        return causes
    
    def find_effects_of(self, node_id: str) -> List[MemoryNode]:
        """Find all nodes caused by the given node"""
        if node_id not in self.node_index:
            return []
        
        node = self.nodes[self.node_index[node_id]]
        effects = []
        for effect_id in node.effects:
            if effect_id in self.node_index:
                effects.append(self.nodes[self.node_index[effect_id]])
        return effects
    
    def why(self, outcome_node_id: str) -> Dict[str, Any]:
        """Answer 'why did this happen?' by tracing causal chain"""
        causes = self.find_causes_of(outcome_node_id)
        explanation = {
            "outcome": outcome_node_id,
            "direct_causes": [c.id for c in causes],
            "causal_chain": [],
            "confidence": 0.0
        }
        
        # Build full causal chain
        chain = []
        to_visit = [(c, 1) for c in causes]  # (node, depth)
        visited = set()
        
        while to_visit:
            current_node, depth = to_visit.pop(0)
            if current_node.id in visited:
                continue
            visited.add(current_node.id)
            
            chain.append({
                "node": current_node.id,
                "type": current_node.node_type.value,
                "content": current_node.content,
                "depth": depth
            })
            
            # Add upstream causes
            upstream = self.find_causes_of(current_node.id)
            for upstream_node in upstream:
                to_visit.append((upstream_node, depth + 1))
        
        explanation["causal_chain"] = chain
        explanation["confidence"] = self._calculate_chain_confidence(chain)
        return explanation
    
    def what_changed(self, before_timestamp: float, after_timestamp: float) -> Dict[str, Any]:
        """Answer 'what changed between these times?'"""
        before_nodes = self.find_before(before_timestamp)
        after_nodes = self.find_after(after_timestamp)
        
        # Find new decisions/outcomes
        new_decisions = [n for n in after_nodes if n.node_type == NodeType.DECISION]
        new_outcomes = [n for n in after_nodes if n.node_type == NodeType.OUTCOME]
        
        return {
            "period_start": before_timestamp,
            "period_end": after_timestamp,
            "new_decisions": [{"id": n.id, "content": n.content} for n in new_decisions],
            "new_outcomes": [{"id": n.id, "content": n.content} for n in new_outcomes],
            "significant_changes": self._detect_significant_changes(before_nodes, after_nodes)
        }
    
    def _calculate_chain_confidence(self, chain: List[Dict]) -> float:
        """Calculate confidence of entire causal chain"""
        if not chain:
            return 0.0
        
        confidences = []
        for item in chain:
            # Find the actual node to get its confidence
            node_id = item["node"]
            if node_id in self.node_index:
                node = self.nodes[self.node_index[node_id]]
                confidences.append(node.confidence)
        
        if not confidences:
            return 0.0
            
        # Geometric mean to penalize weak links
        product = 1.0
        for c in confidences:
            product *= c
        return product ** (1/len(confidences))
    
    def _detect_significant_changes(self, before: List[MemoryNode], after: List[MemoryNode]) -> List[Dict]:
        """Detect significant behavioral changes between periods"""
        changes = []
        
        # Compare decision patterns
        before_decisions = [n for n in before if n.node_type == NodeType.DECISION]
        after_decisions = [n for n in after if n.node_type == NodeType.DECISION]
        
        if len(before_decisions) > 0 and len(after_decisions) > 0:
            # Simple heuristic: if decision frequency doubled/halved
            before_freq = len(before_decisions) / max(1, (before[-1].timestamp - before[0].timestamp))
            after_freq = len(after_decisions) / max(1, (after[-1].timestamp - after[0].timestamp))
            
            ratio = after_freq / before_freq if before_freq > 0 else float('inf')
            if ratio > 2.0 or ratio < 0.5:
                changes.append({
                    "type": "decision_frequency",
                    "change": "increased" if ratio > 1 else "decreased",
                    "ratio": ratio,
                    "description": f"Decision making {'accelerated' if ratio > 1 else 'slowed'} by {abs(ratio-1)*100:.1f}%"
                })
        
        return changes