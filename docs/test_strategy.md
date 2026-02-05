# Test Strategy

## Overview

This document describes the comprehensive testing strategy for the Virtual HIL Framework, covering all levels of testing from unit to integration.

## Test Levels

```
┌─────────────────────────────────────────────────────┐
│                 System Testing                      │
│            (Full ECU Network)                       │
└────────────────────┬────────────────────────────────┘
                     │
┌────────────────────▼────────────────────────────────┐
│               Integration Testing                   │
│         (ECU + CAN + Diagnostics)                  │
└────────────────────┬────────────────────────────────┘
                     │
┌────────────────────▼────────────────────────────────┐
│                Functional Testing                   │
│              (Individual ECU Features)              │
└────────────────────┬────────────────────────────────┘
                     │
┌────────────────────▼────────────────────────────────┐
│                 Unit Testing                        │
│           (Library & Component Functions)           │
└─────────────────────────────────────────────────────┘
```

## Test Categories

### 1. Unit Tests

**Location**: `tests/unit/` (pytest)

**Scope**: Individual functions and classes

**Examples**:
- Cell voltage calculation
- SOC estimation algorithms
- CAN message parsing
- DTC encoding/decoding

**Execution**:
```bash
uv run pytest tests/unit/ -v
```

### 2. Functional Tests

**Location**: `tests/functional/`

**Scope**: Individual ECU features

**Test Suites**:

#### Battery Monitoring (`test_battery_monitoring.robot`)
- Initial state verification
- Cell voltage reading
- Pack parameters
- SOC accuracy
- Temperature monitoring

#### Cell Balancing (`test_cell_balancing.robot`)
- Balancing trigger conditions
- Voltage spread reduction
- Balancing speed
- Impact on average voltage
- Integration with charging

#### Thermal Management (`test_thermal_management.robot`)
- Temperature monitoring
- Overtemperature detection
- Undertemperature detection
- Thermal gradient detection
- Thermal recovery

**Execution**:
```bash
uv run robot --pythonpath ./libraries:./ecu_simulation --outputdir reports tests/functional/
```

### 3. Integration Tests

**Location**: `tests/integration/`

**Scope**: ECU interactions via CAN bus

**Test Areas**:
- CAN message exchange
- Multi-ECU scenarios
- Diagnostic communication
- Fault propagation

**Example Test**:
```robot
Integration - Battery to Door via CAN
    Start Battery Simulation
    Start Door Simulation
    Start CAN Interface

    # Simulate low voltage event
    Set Cell Voltage    cell_id=0    voltage=2.5
    ${faults}=    Get Battery Faults

    # Verify fault indication on CAN
    Wait For CAN Message    can_id=${CAN_BMS_FAULT_ID}    timeout=2
```

### 4. Diagnostic Tests

**Location**: `tests/diagnostic/`

**Scope**: UDS diagnostic services

**Test Areas**:
- Session control
- DID read/write
- DTC handling
- Security access
- Routine execution

**Example Test**:
```robot
Diagnostic - Read DID
    Start Diagnostic Session

    Read Data Identifier    did=0xF19E
    ${data}=    Read Data Identifier    did=0xF19E

    Should Not Be Empty    ${data}
```

### 5. Fault Injection Tests

**Location**: `tests/fault_injection/`

**Scope**: Fault detection and recovery

**Test Areas**:
- Single fault injection
- Multiple simultaneous faults
- Fault clearing
- Fault propagation
- Degraded mode operation

**Example Test**:
```robot
Fault Injection - Overvoltage Recovery
    Start Battery Simulation
    ${initial_soc}=    Get Battery SOC

    # Inject fault
    Inject Cell Overvoltage    cell_id=0    voltage=4.3
    ${detected}=    Verify Battery Fault Detected    OVERVOLTAGE

    # Clear fault
    Set Cell Voltage    cell_id=0    voltage=3.7
    ${cleared}=    Verify No Battery Faults

    Should Be True    ${detected}
    Should Be True    ${cleared}
```

## Test Data Management

### Test Fixtures

**Location**: `resources/test_data.robot`

**Contains**:
- Charging profiles
- Cell imbalance scenarios
- Temperature test points
- Fault scenarios
- CAN message templates

### Configuration Variables

**Location**: `resources/ecu_variables.robot`

**Contains**:
- ECU limits and thresholds
- CAN message IDs
- Diagnostic codes
- Timing parameters

## Test Execution

### Local Development

```bash
# Run all tests
uv run robot --pythonpath ./libraries:./ecu_simulation --outputdir reports tests/

# Run specific suite
uv run robot --pythonpath ./libraries:./ecu_simulation --outputdir reports tests/functional/test_battery_monitoring.robot

# Run with tags
uv run robot --pythonpath ./libraries:./ecu_simulation --outputdir reports --include smoke tests/

# Dry run (syntax check)
uv run robot --dryrun --pythonpath ./libraries:./ecu_simulation tests/
```

### Docker

```bash
# Start all ECUs
docker-compose up -d

# Run tests
docker-compose --profile test run --rm test-runner

# View logs
docker-compose logs -f
```

### CI/CD

**Workflows**:
- `.github/workflows/sil-ci.yml` - Push/PR validation
- `.github/workflows/nightly-regression.yml` - Daily full regression
- `.github/workflows/manual-hil-test.yml` - On-demand testing

## Test Reporting

### Robot Framework Reports

**Generated in**: `reports/`

**Files**:
- `output.xml` - Machine-readable results
- `log.html` - Detailed execution log
- `report.html` - Summary report

### Coverage Reports

```bash
# Generate coverage
uv run pytest --cov=libraries --cov-report=html tests/unit/

# View report
open htmlcov/index.html
```

### Log Analysis

```bash
# Analyze test logs
python scripts/analyze_logs.py reports/output.xml --output test_report.json

# Extract statistics
python scripts/extract_stats.py reports/output.xml --output stats.json
```

## Test Maintenance

### Adding New Tests

1. **Choose appropriate location** based on test scope
2. **Create test file** with descriptive name
3. **Add documentation** at top of file
4. **Use resource files** for common keywords
5. **Tag appropriately** for filtering

### Test Tags

| Tag | Purpose | Example |
|-----|---------|---------|
| `smoke` | Quick validation of basic functionality | Battery initial state |
| `critical` | Core functionality that must work | SOC reading |
| `battery` | Battery ECU tests | Cell balancing |
| `door` | Door ECU tests | Lock/unlock |
| `diagnostic` | UDS diagnostic tests | DID read |
| `fault` | Fault injection tests | Overvoltage |
| `slow` | Long-running tests (>30s) | Full charge cycle |
| `integration` | Multi-ECU tests | CAN messaging |

### Test Review Checklist

- [ ] Test has clear documentation
- [ ] Test follows naming conventions
- [ ] Test uses appropriate resource files
- [ ] Test is tagged correctly
- [ ] Test has assertions for all conditions
- [ ] Test cleans up after itself
- [ ] Test is deterministic (no random failures)
- [ ] Test runs in reasonable time (<60s preferred)

## Continuous Improvement

### Metrics to Track

1. **Test Pass Rate**: Target > 95%
2. **Test Execution Time**: Monitor trends
3. **Code Coverage**: Target > 80%
4. **Flaky Test Rate**: Target < 2%
5. **Test Maintenance Effort**: Time spent on fixes

### Regular Activities

- **Weekly**: Review failed tests, update documentation
- **Monthly**: Review coverage gaps, add new tests
- **Quarterly**: Review test strategy, update as needed

## Troubleshooting

### Common Issues

**Issue**: Test fails intermittently
- **Solution**: Add explicit waits, check timing dependencies

**Issue**: Test passes locally but fails in CI
- **Solution**: Check environment differences, add missing dependencies

**Issue**: Cannot connect to ECU
- **Solution**: Verify ECU started, check CAN interface

**Issue**: DTC not cleared after test
- **Solution**: Add teardown to clear all faults

## Best Practices

1. **Keep tests independent** - No inter-test dependencies
2. **Use teardown** - Always clean up state
3. **Make tests readable** - Use descriptive names and comments
4. **Avoid hard-coding** - Use variables from resource files
5. **Test behavior, not implementation** - Focus on observable outcomes
6. **Use appropriate waits** - Avoid sleep when possible
7. **Log relevant data** - Help with debugging
8. **Review and refactor** - Keep tests maintainable
