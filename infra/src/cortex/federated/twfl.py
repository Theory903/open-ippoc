"""
Trust-Weighted Federated Learning (TWFL)
Enables collective learning without sharing raw data
"""

import asyncio
import numpy as np
from typing import Dict, List, Tuple, Optional, Any
from dataclasses import dataclass, field
import hashlib
import json
from collections import defaultdict
import time

@dataclass
class ModelUpdate:
    """Represents a model gradient/update from a participant"""
    participant_id: str
    gradients: Dict[str, np.ndarray]
    timestamp: float = field(default_factory=time.time)
    loss: float = 0.0
    sample_count: int = 0
    
    def to_dict(self) -> Dict[str, Any]:
        return {
            "participant_id": self.participant_id,
            "gradients": {k: v.tolist() for k, v in self.gradients.items()},
            "timestamp": self.timestamp,
            "loss": self.loss,
            "sample_count": self.sample_count
        }
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'ModelUpdate':
        return cls(
            participant_id=data["participant_id"],
            gradients={k: np.array(v) for k, v in data["gradients"].items()},
            timestamp=data["timestamp"],
            loss=data["loss"],
            sample_count=data["sample_count"]
        )

@dataclass
class TrustMetrics:
    """Trust metrics for federated learning participants"""
    participant_id: str
    reputation_score: float = 0.5
    historical_accuracy: float = 0.5
    contribution_count: int = 0
    last_contribution: float = field(default_factory=time.time)
    anomaly_score: float = 0.0
    
    @property
    def trust_weight(self) -> float:
        """Calculate trust weight for gradient aggregation"""
        # Combine reputation and accuracy with anomaly penalty
        base_weight = 0.6 * self.reputation_score + 0.4 * self.historical_accuracy
        return max(base_weight * (1.0 - self.anomaly_score), 0.1)

class PoisoningDetector:
    """Detects malicious or anomalous model updates"""
    
    def __init__(self, threshold: float = 2.0):
        self.threshold = threshold
        self.baseline_updates: List[ModelUpdate] = []
        self.max_baseline_size = 50
    
    def add_baseline(self, update: ModelUpdate):
        """Add legitimate update to baseline for comparison"""
        self.baseline_updates.append(update)
        if len(self.baseline_updates) > self.max_baseline_size:
            self.baseline_updates.pop(0)
    
    def detect_anomaly(self, update: ModelUpdate) -> Tuple[bool, float]:
        """Detect if update is anomalous"""
        if len(self.baseline_updates) < 5:
            return False, 0.0
        
        # Calculate statistical distance from baseline
        distances = []
        for baseline in self.baseline_updates:
            distance = self._calculate_gradient_distance(update, baseline)
            distances.append(distance)
        
        # Use modified Z-score for outlier detection
        median_dist = np.median(distances)
        mad = np.median([abs(d - median_dist) for d in distances])
        
        if mad == 0:
            return False, 0.0
            
        z_score = abs(np.mean(distances) - median_dist) / (1.4826 * mad)
        is_anomalous = z_score > self.threshold
        anomaly_score = min(z_score / self.threshold, 1.0)
        
        return is_anomalous, anomaly_score
    
    def _calculate_gradient_distance(self, update1: ModelUpdate, update2: ModelUpdate) -> float:
        """Calculate cosine distance between gradient vectors"""
        if not update1.gradients or not update2.gradients:
            return 0.0
        
        # Flatten all gradients into single vectors
        vec1 = np.concatenate([g.flatten() for g in update1.gradients.values()])
        vec2 = np.concatenate([g.flatten() for g in update2.gradients.values()])
        
        # Cosine similarity
        dot_product = np.dot(vec1, vec2)
        norm1 = np.linalg.norm(vec1)
        norm2 = np.linalg.norm(vec2)
        
        if norm1 == 0 or norm2 == 0:
            return 1.0
            
        similarity = dot_product / (norm1 * norm2)
        return 1.0 - similarity

class FederatedLearningCoordinator:
    """Coordinates trust-weighted federated learning across participants"""
    
    def __init__(self, model_template: Dict[str, np.ndarray], 
                 trust_threshold: float = 0.3,
                 poisoning_threshold: float = 2.0):
        self.model_template = model_template
        self.trust_threshold = trust_threshold
        self.global_model = {k: v.copy() for k, v in model_template.items()}
        self.participants: Dict[str, TrustMetrics] = {}
        self.pending_updates: List[ModelUpdate] = []
        self.poisoning_detector = PoisoningDetector(poisoning_threshold)
        self.round_counter = 0
        self.last_sync = time.time()
        
    def register_participant(self, participant_id: str, initial_reputation: float = 0.5) -> None:
        """Register a new participant"""
        if participant_id not in self.participants:
            self.participants[participant_id] = TrustMetrics(
                participant_id=participant_id,
                reputation_score=initial_reputation
            )
    
    def submit_update(self, update: ModelUpdate) -> Dict[str, Any]:
        """Submit model update from participant"""
        # Validate participant exists
        if update.participant_id not in self.participants:
            return {"status": "rejected", "reason": "unknown_participant"}
        
        # Detect poisoning
        is_poisoned, anomaly_score = self.poisoning_detector.detect_anomaly(update)
        
        # Update trust metrics
        trust_metrics = self.participants[update.participant_id]
        trust_metrics.contribution_count += 1
        trust_metrics.last_contribution = time.time()
        trust_metrics.anomaly_score = anomaly_score * 0.9 + trust_metrics.anomaly_score * 0.1
        
        if is_poisoned:
            # Reduce reputation for suspicious behavior
            trust_metrics.reputation_score = max(0.1, trust_metrics.reputation_score * 0.8)
            return {"status": "rejected", "reason": "anomalous_update", "anomaly_score": anomaly_score}
        
        # Add to baseline for future detection
        self.poisoning_detector.add_baseline(update)
        
        # Accept update with trust weight
        self.pending_updates.append(update)
        
        # Increase reputation for good contribution
        trust_metrics.reputation_score = min(1.0, trust_metrics.reputation_score * 1.05)
        
        return {
            "status": "accepted",
            "trust_weight": trust_metrics.trust_weight,
            "anomaly_score": anomaly_score
        }
    
    async def aggregate_round(self, min_participants: int = 3) -> Optional[Dict[str, Any]]:
        """Perform one round of federated aggregation"""
        if len(self.pending_updates) < min_participants:
            return None
        
        self.round_counter += 1
        round_id = f"round_{self.round_counter}_{int(time.time())}"
        
        # Filter updates by trust threshold
        valid_updates = []
        total_weight = 0.0
        
        for update in self.pending_updates:
            trust_metrics = self.participants.get(update.participant_id)
            if trust_metrics and trust_metrics.trust_weight >= self.trust_threshold:
                weight = trust_metrics.trust_weight * update.sample_count
                valid_updates.append((update, weight))
                total_weight += weight
        
        if not valid_updates:
            self.pending_updates.clear()
            return None
        
        # Weighted aggregation
        aggregated_gradients = {}
        for param_name in self.global_model.keys():
            weighted_sum = np.zeros_like(self.global_model[param_name])
            
            for update, weight in valid_updates:
                if param_name in update.gradients:
                    weighted_sum += update.gradients[param_name] * (weight / total_weight)
            
            aggregated_gradients[param_name] = weighted_sum
        
        # Update global model
        learning_rate = 0.01
        for param_name in self.global_model.keys():
            self.global_model[param_name] -= learning_rate * aggregated_gradients[param_name]
        
        # Clear processed updates
        processed_count = len(valid_updates)
        self.pending_updates.clear()
        self.last_sync = time.time()
        
        return {
            "round_id": round_id,
            "participants": len(valid_updates),
            "total_weight": total_weight,
            "processed_updates": processed_count,
            "timestamp": self.last_sync
        }
    
    def get_model_state(self) -> Dict[str, Any]:
        """Get current global model state"""
        return {
            "model": {k: v.tolist() for k, v in self.global_model.items()},
            "round": self.round_counter,
            "last_sync": self.last_sync,
            "participant_count": len(self.participants)
        }
    
    def get_participant_trust(self, participant_id: str) -> Optional[Dict[str, float]]:
        """Get trust metrics for specific participant"""
        if participant_id not in self.participants:
            return None
        
        metrics = self.participants[participant_id]
        return {
            "reputation_score": metrics.reputation_score,
            "historical_accuracy": metrics.historical_accuracy,
            "trust_weight": metrics.trust_weight,
            "anomaly_score": metrics.anomaly_score,
            "contributions": metrics.contribution_count
        }
    
    def get_trust_ranking(self) -> List[Dict[str, Any]]:
        """Get ranking of participants by trustworthiness"""
        rankings = []
        for participant_id, metrics in self.participants.items():
            rankings.append({
                "participant_id": participant_id,
                "trust_weight": metrics.trust_weight,
                "reputation": metrics.reputation_score,
                "accuracy": metrics.historical_accuracy,
                "anomaly_score": metrics.anomaly_score,
                "contributions": metrics.contribution_count
            })
        
        return sorted(rankings, key=lambda x: x["trust_weight"], reverse=True)

# Example usage
async def demo_twfl():
    """Demonstrate TWFL functionality"""
    # Create simple model template
    model_template = {
        "layer1_weights": np.random.randn(10, 5) * 0.1,
        "layer1_bias": np.random.randn(5) * 0.1,
        "layer2_weights": np.random.randn(5, 1) * 0.1,
        "layer2_bias": np.random.randn(1) * 0.1
    }
    
    # Initialize coordinator
    coordinator = FederatedLearningCoordinator(model_template)
    
    # Register participants
    participants = ["node_alpha", "node_beta", "node_gamma", "node_delta"]
    for pid in participants:
        coordinator.register_participant(pid)
    
    # Simulate updates
    for round_num in range(3):
        print(f"\n--- Round {round_num + 1} ---")
        
        # Generate updates from participants
        for pid in participants:
            # Simulate gradient computation
            gradients = {}
            for layer_name, weights in model_template.items():
                noise = np.random.randn(*weights.shape) * 0.01
                gradients[layer_name] = noise
            
            update = ModelUpdate(
                participant_id=pid,
                gradients=gradients,
                loss=np.random.uniform(0.1, 0.5),
                sample_count=np.random.randint(50, 200)
            )
            
            result = coordinator.submit_update(update)
            print(f"{pid}: {result['status']} (trust: {result.get('trust_weight', 0):.3f})")
        
        # Perform aggregation
        result = await coordinator.aggregate_round(min_participants=2)
        if result:
            print(f"Aggregated: {result['participants']} participants, "
                  f"weight: {result['total_weight']:.2f}")
        
        # Show trust rankings
        rankings = coordinator.get_trust_ranking()[:3]
        print("Top trusted participants:")
        for rank, info in enumerate(rankings, 1):
            print(f"  {rank}. {info['participant_id']}: {info['trust_weight']:.3f}")
    
    return coordinator

if __name__ == "__main__":
    asyncio.run(demo_twfl())