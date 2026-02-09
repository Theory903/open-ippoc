# brain/social/trust.py
# @cognitive - IPPOC Social Trust System

from __future__ import annotations

import json
import os
import time
from dataclasses import dataclass, asdict, field
from typing import Dict, Any, Optional


@dataclass
class PeerReputation:
    node_id: str
    trust_score: float = 0.5  # Neutral start
    interactions: int = 0
    last_interaction: float = 0.0
    notes: str = ""

    def update(self, delta: float, reason: str = "") -> None:
        # Clamp between 0.0 and 1.0
        self.trust_score = max(0.0, min(1.0, self.trust_score + delta))
        self.interactions += 1
        self.last_interaction = time.time()
        if reason:
            self.notes = f"{self.notes}; {reason}" if self.notes else reason


class TrustModel:
    """
    Manages the reputation of other nodes in the mesh.
    Used to gatekeep Intents from external sources.
    """
    def __init__(self, path: str = "data/social_trust.json") -> None:
        self.path = path  # Can be env var override
        if os.getenv("SOCIAL_TRUST_PATH"):
            self.path = os.getenv("SOCIAL_TRUST_PATH")
            
        self.peers: Dict[str, PeerReputation] = {}
        self._load()

    def _load(self) -> None:
        if os.path.exists(self.path):
            try:
                with open(self.path, "r", encoding="utf-8") as f:
                    data = json.load(f)
                for pid, pdata in data.get("peers", {}).items():
                    self.peers[pid] = PeerReputation(**pdata)
            except Exception:
                pass

    def _save(self) -> None:
        os.makedirs(os.path.dirname(self.path), exist_ok=True)
        data = {"peers": {pid: asdict(p) for pid, p in self.peers.items()}}
        with open(self.path, "w", encoding="utf-8") as f:
            json.dump(data, f, indent=2)

    def get_trust(self, node_id: str) -> float:
        """Returns trust score for a node. Default 0.5 (Neutral)."""
        if node_id == "self": 
            return 1.0
        if node_id == "system":
            return 1.0
        if node_id == "user": 
            return 1.0 # Blind trust in User for now (Dangerous but practical)
            
        peer = self.peers.get(node_id)
        return peer.trust_score if peer else 0.5

    def update_trust(self, node_id: str, delta: float, reason: str = "") -> None:
        if node_id in ("self", "system", "user"):
            return
            
        if node_id not in self.peers:
            self.peers[node_id] = PeerReputation(node_id=node_id)
            
        self.peers[node_id].update(delta, reason)
        self._save()

    def verify_intent_source(self, source_id: str, min_trust: float = 0.4) -> bool:
        """
        Gatekeeper: Should we listen to this source?
        """
        score = self.get_trust(source_id)
        return score >= min_trust


_trust_instance: TrustModel | None = None

def get_trust_model() -> TrustModel:
    global _trust_instance
    if _trust_instance is None:
        _trust_instance = TrustModel()
    return _trust_instance
