#!/usr/bin/env python3
"""Two-Tower communication service implementation"""

import grpc
from concurrent import futures
import time
import logging
import random
from typing import Dict, List, Optional

import two_tower_pb2
import two_tower_pb2_grpc

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

class TwoTowerService(two_tower_pb2_grpc.TwoTowerServiceServicer):
    """Implementation of Two-Tower communication service"""
    
    def __init__(self):
        # Statistics tracking
        self.total_requests = 0
        self.approved_requests = 0
        self.rejected_requests = 0
        self.total_validation_time = 0.0
        self.risk_distribution: Dict[str, int] = {
            'LOW': 0,
            'MEDIUM': 0,
            'HIGH': 0,
            'CRITICAL': 0
        }
        
    def ValidateAction(self, request: two_tower_pb2.ActionCandidate, context):
        """Send action candidate for validation"""
        start_time = time.time()
        
        logger.info(f"Validating action: {request.action} (Risk: {two_tower_pb2.RiskLevel.Name(request.risk)})")
        
        # Track request statistics
        self.total_requests += 1
        self.risk_distribution[two_tower_pb2.RiskLevel.Name(request.risk)] += 1
        
        # Decision logic based on risk and confidence
        approved = False
        reason = ""
        
        if not request.requires_validation:
            approved = True
            reason = "Action does not require validation"
        else:
            # Decision logic: higher confidence and lower risk = more likely to be approved
            if request.confidence >= 0.8 and request.risk in [two_tower_pb2.RiskLevel.LOW, two_tower_pb2.RiskLevel.MEDIUM]:
                approved = True
                reason = "High confidence and acceptable risk"
            elif request.confidence >= 0.6 and request.risk == two_tower_pb2.RiskLevel.LOW:
                approved = True
                reason = "Medium confidence and low risk"
            elif request.confidence < 0.5:
                approved = False
                reason = "Low confidence"
            elif request.risk == two_tower_pb2.RiskLevel.CRITICAL:
                approved = False
                reason = "Critical risk level"
            else:
                # Random decision for medium confidence/medium risk cases
                approved = random.choice([True, False])
                reason = "Medium confidence and risk - randomized decision"
        
        if approved:
            self.approved_requests += 1
        else:
            self.rejected_requests += 1
        
        # Calculate validation time
        validation_time = time.time() - start_time
        self.total_validation_time += validation_time
        
        # Generate response
        response = two_tower_pb2.ValidationDecision(
            approved=approved,
            reason=reason,
            cost_spent=round(validation_time * 0.1, 3),  # Cost based on time taken
            warnings=self._generate_warnings(request),
            trace_id=request.trace_id,
            timestamp=int(time.time())
        )
        
        logger.info(f"Validation decision for {request.action}: {'APPROVED' if approved else 'REJECTED'}")
        
        return response
    
    def BatchValidateActions(self, request: two_tower_pb2.BatchValidationRequest, context):
        """Batch validation for multiple candidates"""
        logger.info(f"Batch validating {len(request.candidates)} actions")
        
        decisions = []
        for candidate in request.candidates:
            # Reuse ValidateAction logic for each candidate
            decision = self.ValidateAction(candidate, context)
            decisions.append(decision)
        
        return two_tower_pb2.BatchValidationResponse(
            decisions=decisions,
            trace_id=request.trace_id
        )
    
    def GetValidationStats(self, request: two_tower_pb2.ValidationStatsRequest, context):
        """Get validation statistics"""
        logger.info(f"Getting validation stats for period: {request.start_time} to {request.end_time}")
        
        avg_validation_time = 0.0
        if self.total_requests > 0:
            avg_validation_time = self.total_validation_time / self.total_requests
        
        # Convert risk distribution to protobuf format
        risk_distribution = []
        for key, value in self.risk_distribution.items():
            entry = two_tower_pb2.ValidationStatsResponse.RiskDistributionEntry()
            entry.key = key
            entry.value = value
            risk_distribution.append(entry)
        
        response = two_tower_pb2.ValidationStatsResponse()
        response.total_requests = self.total_requests
        response.approved_requests = self.approved_requests
        response.rejected_requests = self.rejected_requests
        response.avg_validation_time = round(avg_validation_time, 4)
        for entry in risk_distribution:
            response.risk_distribution.append(entry)
        
        return response
    
    def _generate_warnings(self, candidate: two_tower_pb2.ActionCandidate) -> List[str]:
        """Generate warnings based on action properties"""
        warnings = []
        
        if candidate.confidence < 0.7:
            warnings.append("Low confidence score")
        
        if candidate.risk in [two_tower_pb2.RiskLevel.HIGH, two_tower_pb2.RiskLevel.CRITICAL]:
            warnings.append("High risk level")
        
        if len(candidate.payload) > 10:
            warnings.append("Large payload size")
        
        return warnings


def serve(port: int = 50051):
    """Start the Two-Tower service server"""
    server = grpc.server(futures.ThreadPoolExecutor(max_workers=10))
    two_tower_pb2_grpc.add_TwoTowerServiceServicer_to_server(TwoTowerService(), server)
    server.add_insecure_port(f'[::]:{port}')
    server.start()
    logger.info(f"Two-Tower service server started on port {port}")
    
    try:
        while True:
            time.sleep(86400)  # Run for 24 hours
    except KeyboardInterrupt:
        logger.info("Shutting down server...")
        server.stop(0)


if __name__ == '__main__':
    serve()
