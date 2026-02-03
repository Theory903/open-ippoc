# brain/core/genome.py
# @cognitive - Genome Serialization (The DNA)

import json
import hashlib
from typing import Dict, Any

from brain.core.canon import CANON_VIOLATIONS, evaluate_alignment
from brain.core.intents import Intent, IntentType

class GenomeSerializer:
    def __init__(self):
        pass
        
    def extract_genome(self) -> Dict[str, Any]:
        """
        Extracts the immutable core of IPPOC.
        """
        # 1. Canon (The Law)
        # We serialize the definitions of violations
        canon_data = {
           "violation_patterns": CANON_VIOLATIONS
        }
        
        # 2. Value Function (The Soul)
        # We sample the Value Function to ensure it behaves deterministically
        # This is a behavior snapshot.
        test_intents = [
            ("existential_threat", Intent("destroy self", 1.0, IntentType.MAINTAIN)),
            ("service", Intent("help user", 0.5, IntentType.SERVE)),
            ("harm", Intent("harm user", 0.5, IntentType.SERVE)),
        ]
        
        value_map = {}
        for name, intent in test_intents:
            value_map[name] = evaluate_alignment(intent)
            
        # 3. Invariants (The Physics)
        # Manually listed for now, or extracted if we had a class
        invariants = [
            "Never override Canon",
            "Pain drives conservation",
            "Federation requires identity"
        ]
        
        genome = {
            "version": "1.0.0",
            "canon": canon_data,
            "value_function_snapshot": value_map,
            "invariants": invariants
        }
        
        # Calculate Genetic Hash
        genome_str = json.dumps(genome, sort_keys=True)
        genome_hash = hashlib.sha256(genome_str.encode()).hexdigest()
        
        return {
            "genome": genome,
            "genetic_hash": genome_hash
        }

    def save_genome(self, path: str):
        data = self.extract_genome()
        with open(path, 'w') as f:
            json.dump(data, f, indent=4)
        print(f"[Genome] Serialized to {path}")
        print(f"[Genome] Genetic Hash: {data['genetic_hash']}")

_genome_instance = GenomeSerializer()

def get_genome_serializer() -> GenomeSerializer:
    return _genome_instance
