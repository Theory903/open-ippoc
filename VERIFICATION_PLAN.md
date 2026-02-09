# IPPOC v1.0.0 Verification Plan

## 1. Automated Tests

### 1.1 Installation Verification
- Test that `install.sh` creates the correct structure in `~/.ippoc`
- Verify virtual environment is properly created
- Check that CLI shim is installed in `~/.local/bin`
- Validate instance directories are created

### 1.2 Service Startup
- Test `ippoc run` command
- Verify Soma health check responds correctly
- Check Cortex readiness probe
- Validate cognitive stream endpoint `/v1/cognitive/stream`

### 1.3 Capability Enforcement (CAP-01)
- Simulate a SENSOR trying to write to forbidden paths
- Test an ACTOR exceeding memory limits
- Verify AUDITOR role permissions

## 2. Manual Verification

### 2.1 Supervisor Hierarchy
1. Start IPPOC with `ippoc run`
2. Kill Soma process
3. Verify Cortex is immediately terminated by supervisor

### 2.2 OpenClaw Integration
1. Launch OpenClaw
2. Verify discovery of IPPOC instance
3. Test cognitive stream integration
4. Validate neural interface communication

### 2.3 Isolation Check
1. Verify all runtime state, logs, and databases are stored in `~/.ippoc/instances/main/`
2. Check that processes are running in the isolated virtual environment
3. Validate file system access restrictions

## 3. Test Execution

### 3.1 Running Tests
```bash
# Run automated tests
pytest test_ippoc.py

# Run manual supervisor hierarchy test
ippoc run &
sleep 10
pkill soma
# Verify Cortex is terminated
```

### 3.2 Expected Results
- All automated tests should pass
- Soma should respond with `health: OK`
- Cortex should fail startup without Soma
- Cognitive stream should provide real-time data

## 4. Failure Scenarios

### 4.1 Installation Issues
- If virtual environment creation fails, check Python version (must be 3.10+)
- If CLI shim is not found, verify `~/.local/bin` is in PATH

### 4.2 Service Startup Issues
- Check logs in `~/.ippoc/instances/main/logs/` for errors
- Verify Redis connection if using external queue

## 5. Cleanup

```bash
# Cleanup installation
rm -rf ~/.ippoc
rm -f ~/.local/bin/ippoc
```

## 6. Validation Report

After executing all tests, complete the validation report:

| Test Category | Test Case | Result | Notes |
|---------------|-----------|--------|-------|
| Installation | Virtual Environment Creation | Pass/Fail | |
| Installation | CLI Shim Installation | Pass/Fail | |
| Services | Soma Health Check | Pass/Fail | |
| Services | Cortex Readiness | Pass/Fail | |
| Services | Cognitive Stream | Pass/Fail | |
| Enforcement | SENSOR Write Violation | Pass/Fail | |
| Enforcement | ACTOR Memory Limit | Pass/Fail | |
| Supervisor | Soma Failure Handling | Pass/Fail | |
| Integration | OpenClaw Discovery | Pass/Fail | |
| Isolation | Runtime State Location | Pass/Fail | |
