# Two-Tower Service

## Overview

The TwoTowerService is a gRPC communication service that implements a two-tower architecture for action validation and decision-making. The service provides methods for validating individual actions, batch validating multiple actions, and collecting validation statistics.

## Service Methods

### 1. ValidateAction
Sends an action candidate for validation. The validation decision is based on:
- Action type and properties
- Risk level
- Confidence score
- Payload content

### 2. BatchValidateActions
Performs batch validation for multiple action candidates in a single request.

### 3. GetValidationStats
Retrieves validation statistics including:
- Total requests
- Approved/rejected requests
- Average validation time
- Risk distribution

## Architecture

### Tower A (Impulse)
Fast, cheap, heuristic/small model for initial action generation.

### Tower B (Validator)
Slow, deliberate, reasoning model for validating high-risk actions.

## Files

- `two_tower.proto`: Protocol buffer definition file
- `two_tower_pb2.py`: Generated Python code from the proto file
- `two_tower_pb2_grpc.py`: Generated gRPC stub and servicer
- `two_tower_client.py`: High-level Python client library with simplified API
- `test_two_tower.py`: Basic Python bindings test
- `test_two_tower_service.py`: Integration test for the gRPC service
- `test_two_tower_client.py`: Comprehensive test file for the client library
- `../two_tower.py`: Main service implementation

## Running the Service

```bash
cd /Users/abhishekjha/CODE/ippoc/src/cortex
python3 two_tower.py
```

The service will start on port 50051.

## Python Client Library

### Installation

Ensure you have the required dependencies:

```bash
pip install grpcio>=1.78.0 grpcio-tools>=1.78.0
```

### Basic Usage

```python
from two_tower_client import TwoTowerClient, ActionCandidate, RiskLevel

# Create client
client = TwoTowerClient(host='localhost', port=50051)
client.connect()

# Validate an action
candidate = ActionCandidate(
    action="safe_action",
    confidence=0.9,
    risk=RiskLevel.LOW,
    payload={"key": "value"}
)
decision = client.validate_action(candidate)
print(f"Action '{candidate.action}' {'APPROVED' if decision.approved else 'REJECTED'}")

# Batch validation
candidates = [
    ActionCandidate(
        action="action1",
        confidence=0.85,
        risk=RiskLevel.MEDIUM,
        payload={"data": "content"}
    ),
    ActionCandidate(
        action="action2",
        confidence=0.95,
        risk=RiskLevel.LOW,
        payload={"info": "data"}
    )
]
decisions = client.batch_validate_actions(candidates)

# Get validation stats
stats = client.get_validation_stats()
print(f"Total requests: {stats.total_requests}")

# Close connection
client.close()
```

### Using Context Manager

```python
from two_tower_client import TwoTowerClient, ActionCandidate, RiskLevel

with TwoTowerClient('localhost', 50051) as client:
    candidate = ActionCandidate(
        action="context_test",
        confidence=0.8,
        risk=RiskLevel.LOW
    )
    decision = client.validate_action(candidate)
    print(decision.approved)
```

### Async Usage

```python
from two_tower_client import create_client, ActionCandidate, RiskLevel

client = create_client()

# Async validation
candidate = ActionCandidate(
    action="async_action",
    confidence=0.9,
    risk=RiskLevel.LOW
)
future = client.validate_action_async(candidate)
decision = future.result()
print(f"Async result: {decision.approved}")

# Async batch validation
candidates = [ActionCandidate("batch1", 0.8, RiskLevel.MEDIUM), 
              ActionCandidate("batch2", 0.9, RiskLevel.LOW)]
future = client.batch_validate_actions_async(candidates)
decisions = future.result()
```

### Quick Validation Function

```python
from two_tower_client import validate_action_simple, RiskLevel

decision = validate_action_simple(
    action="quick_test",
    confidence=0.85,
    risk=RiskLevel.MEDIUM,
    payload={"test": "data"}
)
print(f"Approved: {decision.approved}")
```

## Client Features

- **Simplified API**: High-level abstractions over gRPC calls
- **Connection Management**: Auto-connect, reconnection, and context manager support
- **Error Handling**: Custom exceptions for different failure scenarios
- **Retry Logic**: Exponential backoff for transient failures
- **Async Support**: Thread-based async operations
- **Type Safety**: Dataclass-based models with type annotations
- **Statistics Tracking**: Built-in methods to retrieve validation metrics
- **Batch Operations**: Efficient batch processing of multiple candidates

## Testing

### Basic Bindings Test
```bash
cd /Users/abhishekjha/CODE/ippoc/src/cortex/proto
python3 test_two_tower.py
```

### Service Integration Test (Requires running service)
```bash
cd /Users/abhishekjha/CODE/ippoc/src/cortex/proto
python3 test_two_tower_service.py
```

### Client Library Test
```bash
cd /Users/abhishekjha/CODE/ippoc/src/cortex/proto
python3 test_two_tower_client.py
```

### Quick Test (Check service availability)
```bash
cd /Users/abhishekjha/CODE/ippoc/src/cortex/proto
python3 test_two_tower_client.py --quick
```

## Requirements

```
grpcio>=1.78.0
grpcio-tools>=1.78.0
```
