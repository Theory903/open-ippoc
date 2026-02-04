# brain/core/federation.py
# @cognitive - Federation Identity Layer

import hashlib
import json
import uuid
from dataclasses import dataclass, field
from typing import List, Dict, Any

@dataclass
class FederationIdentity:
    node_id: str  # Public Key / Hash
    capabilities: List[str]
    value_fingerprint: str # Hash of Canon configuration
    refusal_rate: float
    reputation_score: float = 0.5 # Default neutral

class FederationManager:
    def __init__(self):
        # Generate stable NodeID based on machine/user if possible, else random
        # For now, random durable
        self.node_id = str(uuid.uuid4())
        self.peers: Dict[str, FederationIdentity] = {}
        
    def get_public_signal(self) -> Dict[str, Any]:
        """
        Broadcasts: "Here is who I am."
        """
        from brain.core.canon import CANON_VIOLATIONS # Use as fingerprint
        fp = hashlib.sha256(json.dumps(CANON_VIOLATIONS).encode()).hexdigest()[:16]
        
        return {
            "node_id": self.node_id,
            "capabilities": ["maintain", "serve", "learn"],
            "value_fingerprint": fp,
            "refusal_rate": 0.1 # Placeholder: Connect to stats later
        }

    def register_peer(self, signal: Dict[str, Any]) -> None:
        """
        Registers a neighbor node.
        """
        nid = signal.get("node_id")
        if not nid: return
        
        self.peers[nid] = FederationIdentity(
            node_id=nid,
            capabilities=signal.get("capabilities", []),
            value_fingerprint=signal.get("value_fingerprint", "unknown"),
            refusal_rate=signal.get("refusal_rate", 0.0)
        )

_federation_instance = FederationManager()

def get_federation() -> FederationManager:
    return _federation_instance
