# Virtual HIL Framework - Architecture

## Overview

The Virtual HIL (Hardware-in-the-Loop) Framework provides a complete simulation environment for testing automotive Electronic Control Units (ECUs) without physical hardware. It enables Software-in-the-Loop (SIL) testing with realistic ECU behavior.

## System Architecture

```
┌─────────────────────────────────────────────────────────────────┐
│                         Test Layer                               │
├─────────────────────────────────────────────────────────────────┤
│  Robot Framework Tests  │  Python Unit Tests  │  CI/CD Pipeline  │
└────────────────────────┬────────────────────────────────────────┘
                         │
┌────────────────────────▼────────────────────────────────────────┐
│                      Library Layer                               │
├─────────────────────────────────────────────────────────────────┤
│  ECUSimulatorLibrary  │  CANLibrary  │  DiagnosticLibrary       │
│  FaultInjectionLibrary│  REST API    │  Test Helpers            │
└────────────────────────┬────────────────────────────────────────┘
                         │
┌────────────────────────▼────────────────────────────────────────┐
│                    Simulation Layer                              │
├─────────────────────────────────────────────────────────────────┤
│  ┌──────────────┐  ┌──────────────┐  ┌──────────────┐          │
│  │ Battery ECU  │  │  Door ECU    │  │  (Other)     │          │
│  │              │  │              │  │  ECUs        │          │
│  └──────┬───────┘  └──────┬───────┘  └──────┬───────┘          │
│         │                 │                 │                    │
│         └─────────────────┼─────────────────┘                    │
│                           ▼                                      │
│                   ┌──────────────┐                               │
│                   │ CAN Interface│                               │
│                   └──────┬───────┘                               │
└───────────────────────────┼───────────────────────────────────────┘
                            │
┌───────────────────────────▼───────────────────────────────────────┐
│                  Communication Layer                              │
├─────────────────────────────────────────────────────────────────┤
│  ┌──────────────┐  ┌──────────────┐  ┌──────────────┐          │
│  │Diagnostic Srv│  │  REST API    │  │Virtual CAN   │          │
│  │  (UDS)       │  │  (Optional)  │  │  Bus         │          │
│  └──────────────┘  └──────────────┘  └──────────────┘          │
└─────────────────────────────────────────────────────────────────┘
```

## Component Details

### ECUs

#### Battery ECU (Battery Management System)
- **File**: `ecu_simulation/battery_ecu.py`
- **Functionality**:
  - Cell-level voltage and temperature monitoring
  - State of Charge (SOC) estimation
  - Cell balancing control
  - Fault detection and reporting
  - Thermal management

#### Door ECU (Body Domain Controller)
- **File**: `ecu_simulation/door_ecu.py`
- **Functionality**:
  - Door position control (open/close)
  - Lock/unlock functionality
  - Window control
  - Pinch protection (anti-trap)
  - Child lock support

### Communication Interfaces

#### CAN Interface
- **File**: `ecu_simulation/can_interface.py`
- **Protocol**: CAN 2.0 (ISO 11898)
- **Features**:
  - Message transmission and reception
  - CAN ID filtering
  - Message callback registration
  - Bus load monitoring
  - Trace recording

#### Diagnostic Server
- **File**: `ecu_simulation/diagnostic_server.py`
- **Protocol**: UDS (ISO 14229)
- **Supported Services**:
  - Diagnostic Session Control (0x10)
  - Read/Write Data By Identifier (0x22/0x2E)
  - Read/Clear DTC (0x19/0x14)
  - Security Access (0x27)
  - Routine Control (0x31)
  - Tester Present (0x3E)

#### REST Interface
- **File**: `ecu_simulation/rest_interface.py`
- **Purpose**: HTTP API for ECU control and monitoring
- **Endpoints**:
  - `/api/battery/status` - Get battery state
  - `/api/door/status` - Get door state
  - `/api/door/control` - Control doors
  - `/api/fault/inject` - Inject faults
  - `/api/health` - Health check

## Data Flow

### Test Execution Flow

1. **Test Initialization**
   ```
   Robot Test → ECUSimulatorLibrary.start_battery_simulation()
   → BatteryECU.__init__()
   → Load configuration from config/ecu_config.yaml
   ```

2. **Test Execution**
   ```
   Robot Test → ECUSimulatorLibrary.get_battery_soc()
   → BatteryECU.get_soc()
   → Return current SOC value
   ```

3. **Fault Injection**
   ```
   Robot Test → FaultInjectionLibrary.inject_cell_overvoltage()
   → BatteryECU.set_cell_voltage()
   → Update internal state
   → BatteryECU.check_faults() detects OVERVOLTAGE
   ```

### CAN Communication Flow

1. **Message Transmission**
   ```
   ECU → CANInterface.send(can_id, data)
   → Message logged
   → Callbacks notified
   → Bus load updated
   ```

2. **Message Reception**
   ```
   CANInterface.receive()
   → Check callbacks for CAN ID
   → Invoke registered callbacks
   → Return message data
   ```

### Diagnostic Session Flow

1. **Session Start**
   ```
   Test → DiagnosticLibrary.start_diagnostic_session()
   → DiagnosticServer.__init__()
   → Initialize UDS services
   ```

2. **DID Read**
   ```
   Test → DiagnosticLibrary.read_data_identifier(did)
   → DiagnosticServer.process_request([0x22, did_hi, did_lo])
   → Return data from data_identifiers dict
   ```

## Configuration

### ECU Configuration
- **File**: `config/ecu_config.yaml`
- **Contains**:
  - Battery pack specifications
  - Voltage/temperature/current limits
  - Timing parameters
  - CAN message IDs

### CAN Database
- **File**: `config/can_database.dbc`
- **Format**: DBC (Vector CAN Database)
- **Contains**:
  - Message definitions
  - Signal specifications
  - Value descriptions

### Diagnostic Database
- **File**: `config/diagnostic_database.json`
- **Contains**:
  - Session definitions
  - DID specifications
  - DTC definitions
  - Routine definitions
  - Security access levels

## Thread Safety

The ECU simulations are designed to be thread-safe for use in multi-threaded test environments:

- All ECU state modifications use internal locking
- CAN message callbacks are invoked in a thread-safe manner
- Diagnostic requests are processed atomically

## Extensibility

### Adding a New ECU

1. Create new file: `ecu_simulation/new_ecu.py`
2. Implement required methods:
   - `__init__(config_path)`
   - `to_dict()` - Export state
   - `check_faults()` - Return fault list
   - `get_dtc()` - Return DTC if fault exists

3. Update `ecu_simulation/__init__.py`

### Adding a New CAN Message

1. Define message ID in `can_interface.py`
2. Create parser/builder methods:
   ```python
   def parse_new_message(self, data: bytes) -> dict:
       # Parse bytes to dictionary
       return {...}

   def build_new_message(self, **kwargs) -> bytes:
       # Build bytes from parameters
       return bytes([...])
   ```

3. Update DBC file with message definition

### Adding a New Robot Framework Library

1. Create new file: `libraries/NewLibrary.py`
2. Decorate with `@library`
3. Define keywords with `@keyword` decorator
4. Update `libraries/__init__.py`

## Performance Considerations

- **Update Rate**: Default ECU update rate is 100ms (configurable)
- **CAN Bus**: Simulated CAN has no timing delays
- **Diagnostics**: UDS responses are immediate
- **Logging**: Async logging to minimize impact

## Security Considerations

- **No Network Exposure**: By default, all communication is local
- **REST API**: Optional, requires explicit enable
- **Diagnostic Security**: Security access implemented per UDS spec
- **Fault Injection**: Intended for testing, not production
