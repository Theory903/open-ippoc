#!/usr/bin/env python3
"""Two-Tower Service Python Client Library

A high-level client API that simplifies communication with the TwoTowerService gRPC service.
Provides methods for validating actions, batch validation, and retrieving statistics with
built-in error handling, connection management, and retry logic.
"""

import grpc
import time
import logging
from typing import Optional, List, Dict, Any, Tuple
from concurrent import futures
from dataclasses import dataclass
from enum import Enum

import two_tower_pb2
import two_tower_pb2_grpc

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


class RiskLevel(Enum):
    """Risk level enumeration for action candidates"""
    LOW = two_tower_pb2.RiskLevel.LOW
    MEDIUM = two_tower_pb2.RiskLevel.MEDIUM
    HIGH = two_tower_pb2.RiskLevel.HIGH
    CRITICAL = two_tower_pb2.RiskLevel.CRITICAL

    @classmethod
    def from_string(cls, value: str) -> 'RiskLevel':
        """Convert string to RiskLevel enum"""
        return cls[value.upper()]


@dataclass
class ActionCandidate:
    """Data class representing an action candidate for validation"""
    action: str
    confidence: float
    risk: RiskLevel
    payload: Dict[str, str] = None
    requires_validation: bool = True
    trace_id: str = None
    timestamp: int = None

    def to_proto(self) -> two_tower_pb2.ActionCandidate:
        """Convert to protobuf message"""
        payload = self.payload or {}
        trace_id = self.trace_id or f"trace_{int(time.time() * 1000)}"
        timestamp = self.timestamp or int(time.time())

        return two_tower_pb2.ActionCandidate(
            action=self.action,
            confidence=self.confidence,
            risk=self.risk.value,
            payload=payload,
            requires_validation=self.requires_validation,
            trace_id=trace_id,
            timestamp=timestamp
        )

    @classmethod
    def from_proto(cls, proto: two_tower_pb2.ActionCandidate) -> 'ActionCandidate':
        """Create from protobuf message"""
        return cls(
            action=proto.action,
            confidence=proto.confidence,
            risk=RiskLevel(proto.risk),
            payload=dict(proto.payload),
            requires_validation=proto.requires_validation,
            trace_id=proto.trace_id,
            timestamp=proto.timestamp
        )


@dataclass
class ValidationDecision:
    """Data class representing a validation decision"""
    approved: bool
    reason: str
    cost_spent: float
    warnings: List[str] = None
    trace_id: str = None
    timestamp: int = None

    @classmethod
    def from_proto(cls, proto: two_tower_pb2.ValidationDecision) -> 'ValidationDecision':
        """Create from protobuf message"""
        return cls(
            approved=proto.approved,
            reason=proto.reason,
            cost_spent=proto.cost_spent,
            warnings=list(proto.warnings),
            trace_id=proto.trace_id,
            timestamp=proto.timestamp
        )


@dataclass
class ValidationStats:
    """Data class representing validation statistics"""
    total_requests: int
    approved_requests: int
    rejected_requests: int
    avg_validation_time: float
    risk_distribution: Dict[str, int]

    @classmethod
    def from_proto(cls, proto: two_tower_pb2.ValidationStatsResponse) -> 'ValidationStats':
        """Create from protobuf message"""
        risk_distribution = {entry.key: entry.value for entry in proto.risk_distribution}
        return cls(
            total_requests=proto.total_requests,
            approved_requests=proto.approved_requests,
            rejected_requests=proto.rejected_requests,
            avg_validation_time=proto.avg_validation_time,
            risk_distribution=risk_distribution
        )


class TwoTowerClientError(Exception):
    """Base exception for TwoTowerClient errors"""
    pass


class ConnectionError(TwoTowerClientError):
    """Connection-related errors"""
    pass


class ServiceError(TwoTowerClientError):
    """Service-related errors"""
    pass


class ValidationError(TwoTowerClientError):
    """Validation-related errors"""
    pass


class TwoTowerClient:
    """High-level client for interacting with the TwoTowerService"""

    def __init__(
        self,
        host: str = 'localhost',
        port: int = 50051,
        max_retries: int = 3,
        retry_delay: float = 0.5,
        timeout: float = 30.0,
        max_workers: int = 10
    ):
        """
        Initialize the TwoTowerClient.

        Args:
            host: gRPC service host (default: localhost)
            port: gRPC service port (default: 50051)
            max_retries: Maximum number of retries on failure (default: 3)
            retry_delay: Delay between retries in seconds (default: 0.5)
            timeout: Request timeout in seconds (default: 30.0)
            max_workers: Number of worker threads for async operations (default: 10)
        """
        self.host = host
        self.port = port
        self.max_retries = max_retries
        self.retry_delay = retry_delay
        self.timeout = timeout
        self.max_workers = max_workers
        self.channel: Optional[grpc.Channel] = None
        self.stub: Optional[two_tower_pb2_grpc.TwoTowerServiceStub] = None
        self._executor = futures.ThreadPoolExecutor(max_workers=max_workers)

    def connect(self) -> None:
        """Establish connection to the gRPC service"""
        try:
            logger.info(f"Connecting to TwoTowerService at {self.host}:{self.port}")
            self.channel = grpc.insecure_channel(f'{self.host}:{self.port}')
            self.stub = two_tower_pb2_grpc.TwoTowerServiceStub(self.channel)
            self._wait_for_connection()
            logger.info("Successfully connected to TwoTowerService")
        except Exception as e:
            raise ConnectionError(f"Failed to connect to TwoTowerService: {e}")

    def _wait_for_connection(self, timeout: float = 5.0) -> None:
        """Wait for service to be available"""
        try:
            grpc.channel_ready_future(self.channel).result(timeout=timeout)
        except Exception as e:
            raise ConnectionError(f"Service not available: {e}")

    def is_connected(self) -> bool:
        """Check if connected to the service"""
        if not self.channel or not self.stub:
            return False
        try:
            grpc.channel_ready_future(self.channel).result(timeout=1.0)
            return True
        except:
            return False

    def validate_action(
        self,
        candidate: ActionCandidate,
        timeout: Optional[float] = None
    ) -> ValidationDecision:
        """
        Validate a single action candidate.

        Args:
            candidate: Action candidate to validate
            timeout: Optional timeout for the request

        Returns:
            ValidationDecision containing approval result

        Raises:
            TwoTowerClientError: If validation fails
        """
        if not self.is_connected():
            self.connect()

        timeout = timeout or self.timeout

        for attempt in range(self.max_retries + 1):
            try:
                logger.debug(f"Validating action: {candidate.action} (attempt {attempt + 1})")
                proto_candidate = candidate.to_proto()
                proto_response = self.stub.ValidateAction(
                    proto_candidate,
                    timeout=timeout
                )
                decision = ValidationDecision.from_proto(proto_response)
                logger.debug(f"Action {candidate.action} {'' if decision.approved else 'NOT '}approved")
                return decision
            except Exception as e:
                logger.warning(f"Validation attempt {attempt + 1} failed: {e}")
                if attempt == self.max_retries:
                    raise ValidationError(f"Failed to validate action after {self.max_retries + 1} attempts: {e}")
                time.sleep(self.retry_delay * (2 ** attempt))  # Exponential backoff

    def validate_action_async(self, candidate: ActionCandidate) -> futures.Future:
        """
        Validate an action asynchronously.

        Args:
            candidate: Action candidate to validate

        Returns:
            Future object that resolves to ValidationDecision
        """
        return self._executor.submit(self.validate_action, candidate)

    def batch_validate_actions(
        self,
        candidates: List[ActionCandidate],
        trace_id: str = None,
        timeout: Optional[float] = None
    ) -> List[ValidationDecision]:
        """
        Batch validate multiple action candidates.

        Args:
            candidates: List of action candidates to validate
            trace_id: Optional trace ID for the batch request
            timeout: Optional timeout for the request

        Returns:
            List of ValidationDecision objects

        Raises:
            TwoTowerClientError: If batch validation fails
        """
        if not self.is_connected():
            self.connect()

        timeout = timeout or self.timeout
        trace_id = trace_id or f"batch_{int(time.time() * 1000)}"

        for attempt in range(self.max_retries + 1):
            try:
                logger.debug(f"Batch validating {len(candidates)} actions (attempt {attempt + 1})")
                proto_candidates = [c.to_proto() for c in candidates]
                request = two_tower_pb2.BatchValidationRequest(
                    candidates=proto_candidates,
                    trace_id=trace_id
                )
                response = self.stub.BatchValidateActions(request, timeout=timeout)
                decisions = [ValidationDecision.from_proto(d) for d in response.decisions]
                logger.debug(f"Batch validation complete: {len(decisions)} decisions")
                return decisions
            except Exception as e:
                logger.warning(f"Batch validation attempt {attempt + 1} failed: {e}")
                if attempt == self.max_retries:
                    raise ValidationError(f"Failed to batch validate after {self.max_retries + 1} attempts: {e}")
                time.sleep(self.retry_delay * (2 ** attempt))

    def batch_validate_actions_async(
        self,
        candidates: List[ActionCandidate],
        trace_id: str = None
    ) -> futures.Future:
        """
        Batch validate actions asynchronously.

        Args:
            candidates: List of action candidates to validate
            trace_id: Optional trace ID for the batch request

        Returns:
            Future object that resolves to list of ValidationDecision
        """
        return self._executor.submit(self.batch_validate_actions, candidates, trace_id)

    def get_validation_stats(
        self,
        start_time: Optional[int] = None,
        end_time: Optional[int] = None,
        timeout: Optional[float] = None
    ) -> ValidationStats:
        """
        Retrieve validation statistics.

        Args:
            start_time: Optional start timestamp (UNIX time)
            end_time: Optional end timestamp (UNIX time)
            timeout: Optional timeout for the request

        Returns:
            ValidationStats containing statistics

        Raises:
            TwoTowerClientError: If statistics retrieval fails
        """
        if not self.is_connected():
            self.connect()

        timeout = timeout or self.timeout
        start_time = start_time or 0
        end_time = end_time or int(time.time())

        for attempt in range(self.max_retries + 1):
            try:
                logger.debug(f"Retrieving validation stats from {start_time} to {end_time}")
                request = two_tower_pb2.ValidationStatsRequest(
                    start_time=start_time,
                    end_time=end_time
                )
                response = self.stub.GetValidationStats(request, timeout=timeout)
                stats = ValidationStats.from_proto(response)
                logger.debug(f"Stats retrieved: {stats.total_requests} requests")
                return stats
            except Exception as e:
                logger.warning(f"Stats retrieval attempt {attempt + 1} failed: {e}")
                if attempt == self.max_retries:
                    raise ServiceError(f"Failed to retrieve stats after {self.max_retries + 1} attempts: {e}")
                time.sleep(self.retry_delay * (2 ** attempt))

    def get_validation_stats_async(
        self,
        start_time: Optional[int] = None,
        end_time: Optional[int] = None
    ) -> futures.Future:
        """
        Retrieve validation statistics asynchronously.

        Args:
            start_time: Optional start timestamp (UNIX time)
            end_time: Optional end timestamp (UNIX time)

        Returns:
            Future object that resolves to ValidationStats
        """
        return self._executor.submit(self.get_validation_stats, start_time, end_time)

    def close(self) -> None:
        """Close the connection to the service"""
        if self._executor:
            self._executor.shutdown(wait=True)
        if self.channel:
            self.channel.close()
            logger.info("Connection to TwoTowerService closed")

    def __enter__(self):
        """Context manager entry: connect to service"""
        self.connect()
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        """Context manager exit: close connection"""
        self.close()

    def __del__(self):
        """Destructor: ensure connection is closed"""
        if hasattr(self, 'channel') and self.channel:
            self.channel.close()


def create_client(
    host: str = 'localhost',
    port: int = 50051,
    **kwargs
) -> TwoTowerClient:
    """
    Create and connect a TwoTowerClient instance.

    Args:
        host: gRPC service host (default: localhost)
        port: gRPC service port (default: 50051)
        **kwargs: Additional parameters for TwoTowerClient

    Returns:
        Connected TwoTowerClient instance
    """
    client = TwoTowerClient(host, port, **kwargs)
    client.connect()
    return client


def validate_action_simple(
    action: str,
    confidence: float,
    risk: str or RiskLevel,
    payload: Dict[str, str] = None,
    host: str = 'localhost',
    port: int = 50051
) -> ValidationDecision:
    """
    Simple convenience function for validating a single action without creating a client instance.

    Args:
        action: Action name
        confidence: Confidence score (0-1)
        risk: Risk level (string or RiskLevel enum)
        payload: Optional payload
        host: gRPC service host
        port: gRPC service port

    Returns:
        ValidationDecision
    """
    if isinstance(risk, str):
        risk = RiskLevel.from_string(risk)

    candidate = ActionCandidate(
        action=action,
        confidence=confidence,
        risk=risk,
        payload=payload or {}
    )

    with TwoTowerClient(host, port) as client:
        return client.validate_action(candidate)


def main():
    """Example usage of the client library"""
    logger.info("Testing TwoTowerClient library")

    # Create client with default settings
    client = create_client()

    try:
        # Test 1: Validate simple action
        logger.info("\n1. Testing validate_action()")
        candidate1 = ActionCandidate(
            action="safe_action",
            confidence=0.9,
            risk=RiskLevel.LOW,
            payload={"key": "value"},
            requires_validation=True
        )
        decision1 = client.validate_action(candidate1)
        logger.info(f"Action '{candidate1.action}' {'APPROVED' if decision1.approved else 'REJECTED'}")
        logger.info(f"Reason: {decision1.reason}")
        logger.info(f"Cost: ${decision1.cost_spent:.3f}")
        if decision1.warnings:
            logger.info(f"Warnings: {', '.join(decision1.warnings)}")

        # Test 2: Batch validation
        logger.info("\n2. Testing batch_validate_actions()")
        candidates = [
            ActionCandidate(
                action="medium_risk_action",
                confidence=0.7,
                risk=RiskLevel.MEDIUM,
                payload={"data": "some content"},
                requires_validation=True
            ),
            ActionCandidate(
                action="high_risk_action",
                confidence=0.5,
                risk=RiskLevel.HIGH,
                payload={"sensitive": "data"},
                requires_validation=True
            ),
            ActionCandidate(
                action="no_validation_action",
                confidence=0.6,
                risk=RiskLevel.LOW,
                payload={"info": "public"},
                requires_validation=False
            )
        ]
        decisions = client.batch_validate_actions(candidates)
        for i, (candidate, decision) in enumerate(zip(candidates, decisions)):
            logger.info(f"Action {i+1}: '{candidate.action}' -> {'APPROVED' if decision.approved else 'REJECTED'}")

        # Test 3: Get validation stats
        logger.info("\n3. Testing get_validation_stats()")
        stats = client.get_validation_stats()
        logger.info(f"Total requests: {stats.total_requests}")
        logger.info(f"Approved: {stats.approved_requests} ({100 * stats.approved_requests / stats.total_requests:.1f}%)")
        logger.info(f"Rejected: {stats.rejected_requests} ({100 * stats.rejected_requests / stats.total_requests:.1f}%)")
        logger.info(f"Average time: {stats.avg_validation_time:.4f}s")
        logger.info("Risk distribution:")
        for risk, count in stats.risk_distribution.items():
            logger.info(f"  {risk}: {count}")

    except Exception as e:
        logger.error(f"Error: {e}")
    finally:
        client.close()


if __name__ == '__main__':
    main()
