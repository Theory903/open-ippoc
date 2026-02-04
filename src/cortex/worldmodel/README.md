# WorldModel Simulator

## Purpose

The WorldModel is a safe sandbox environment for testing code changes, patches, and new tools before deploying them to production.

## Architecture

```
┌─────────────────────────────────┐
│  Git Evolution / ToolSmith      │
│  (Proposes changes)             │
└────────────┬────────────────────┘
             │
             ▼
┌─────────────────────────────────┐
│  WorldModel Simulator           │
│  - Isolated filesystem          │
│  - Resource limits              │
│  - Scenario testing             │
└────────────┬────────────────────┘
             │
             ▼
        ✅ Success → Deploy
        ❌ Failure → Reject
```

## Usage

```rust
use world_model::WorldModel;

let simulator = WorldModel::new()?;

let result = simulator.simulate_patch(
    "fn optimized() { /* new code */ }",
    "basic_compile"
).await?;

if result.success {
    println!("✅ Patch verified - safe to deploy");
} else {
    println!("❌ Patch failed: {:?}", result.error);
}
```

## Scenarios

- `basic_compile` - Verify code compiles
- `high_load` - Test under stress
- `network_partition` - Test resilience
- Custom scenarios can be added in `src/scenarios/`

## Metrics

Each simulation returns:
- CPU usage
- Memory consumption
- Network calls
- Duration
- Success/failure status
