# ECU Specifications

## Battery Management System (BMS) ECU

### Overview
The Battery ECU simulates a high-voltage battery management system for electric vehicles. It manages a 96-cell battery pack with individual cell monitoring and balancing capabilities.

### Technical Specifications

| Parameter | Value | Unit |
|-----------|-------|------|
| Number of Cells | 96 | cells |
| Configuration | 96S1P | - |
| Cell Capacity | 3.2 | Ah |
| Total Capacity | 307.2 | Ah |
| Nominal Voltage | 3.7 | V/cell |
| Pack Voltage | 355.2 | V |
| Max Voltage | 4.2 | V/cell |
| Min Voltage | 2.8 | V/cell |

### Operating Limits

| Parameter | Min | Max | Unit |
|-----------|-----|-----|------|
| Operating Temperature | -10 | 45 | °C |
| Cell Temperature | -20 | 60 | °C |
| Charge Current | - | 50 | A |
| Discharge Current | - | 100 | A |
| SOC | 0 | 100 | % |

### CAN Messages

#### BMS_Status (0x100) - 100ms period
| Signal | Start Bit | Length | Scale | Offset | Unit | Min | Max |
|--------|-----------|--------|-------|--------|------|-----|-----|
| BMS_SOC | 0 | 8 | 0.5 | 0 | % | 0 | 100 |
| BMS_SOH | 8 | 8 | 1 | 0 | % | 0 | 100 |
| BMS_Voltage | 16 | 16 | 0.1 | 0 | V | 0 | 6553.5 |
| BMS_Current | 32 | 16 | -0.1 | 0 | A | -3276.7 | 3276.7 |
| BMS_Temperature | 48 | 8 | 1 | -40 | °C | -40 | 215 |

#### BMS_Cell_Data (0x101) - 500ms period (multiplexed)
| Signal | Start Bit | Length | Scale | Offset | Unit | Min | Max |
|--------|-----------|--------|-------|--------|------|-----|-----|
| Cell_Mux | 0 | 4 | 1 | 0 | - | 0 | 15 |
| Cell_0_Voltage | 4 | 12 | 0.001 | 0 | V | 0 | 4.095 |
| Cell_1_Voltage | 16 | 12 | 0.001 | 0 | V | 0 | 4.095 |
| Cell_2_Voltage | 28 | 12 | 0.001 | 0 | V | 0 | 4.095 |
| Cell_3_Voltage | 40 | 12 | 0.001 | 0 | V | 0 | 4.095 |
| Cell_4_Voltage | 52 | 12 | 0.001 | 0 | V | 0 | 4.095 |

### Diagnostic Trouble Codes (DTCs)

| DTC | Description | Severity |
|-----|-------------|----------|
| BMS_OVERVOLTAGE_ACTIVE | Cell voltage exceeds maximum | Critical |
| BMS_UNDERVOLTAGE_ACTIVE | Cell voltage below minimum | Critical |
| BMS_OVERTEMPERATURE_ACTIVE | Cell temperature exceeds maximum | Critical |
| BMS_UNDERTEMPERATURE_ACTIVE | Cell temperature below minimum | Warning |
| BMS_LOW_SOC | State of charge below warning level | Warning |

### Data Identifiers (DIDs)

| DID | Name | Type | Read/Write |
|-----|------|------|------------|
| 0xF10C | ECU Serial Number | string | R |
| 0xF187 | Hardware Number | string | R |
| 0xF19E | Software Version | string | R |
| 0xF198 | Supplier ID | string | R |

---

## Body Domain Controller (BDC) / Door ECU

### Overview
The Door ECU simulates a body domain controller managing four vehicle doors with integrated window lifters and locking mechanisms.

### Technical Specifications

| Parameter | Value | Unit |
|-----------|-------|------|
| Number of Doors | 4 | - |
| Door Types | FL, FR, RL, RR | - |
| Full Open Time | 2.0 | s |
| Full Close Time | 2.5 | s |
| Window Open Time | 4.0 | s |
| Position Resolution | 5 | % |

### Door States

| State | Description |
|-------|-------------|
| CLOSED | Door fully closed |
| OPENING | Door opening |
| OPEN | Door fully open |
| CLOSING | Door closing |
| BLOCKED | Obstruction detected |
| FAULT | ECU fault state |

### Lock States

| State | Description |
|-------|-------------|
| LOCKED | Door locked |
| UNLOCKED | Door unlocked |
| CHILD_LOCKED | Child lock engaged |

### CAN Messages

#### BDC_Door_Status (0x200) - 100ms period
| Signal | Bit | Description |
|--------|-----|-------------|
| FL_Open | 0 | Front left open |
| FR_Open | 1 | Front right open |
| RL_Open | 2 | Rear left open |
| RR_Open | 3 | Rear right open |
| FL_Locked | 8 | Front left locked |
| FR_Locked | 9 | Front right locked |
| RL_Locked | 10 | Rear left locked |
| RR_Locked | 11 | Rear right locked |

#### BDC_Door_Position (0x201) - 50ms period
| Signal | Start Bit | Length | Scale | Offset | Unit | Min | Max |
|--------|-----------|--------|-------|--------|------|-----|-----|
| FL_Position | 0 | 7 | 1 | 0 | % | 0 | 100 |
| FL_State | 7 | 3 | 1 | 0 | - | 0 | 7 |
| FR_Position | 10 | 7 | 1 | 0 | % | 0 | 100 |
| FR_State | 17 | 3 | 1 | 0 | - | 0 | 7 |
| RL_Position | 20 | 7 | 1 | 0 | % | 0 | 100 |
| RL_State | 27 | 3 | 1 | 0 | - | 0 | 7 |
| RR_Position | 30 | 7 | 1 | 0 | % | 0 | 100 |
| RR_State | 37 | 3 | 1 | 0 | - | 0 | 7 |

#### BDC_Window_Position (0x202) - 100ms period
| Signal | Start Bit | Length | Scale | Offset | Unit | Min | Max |
|--------|-----------|--------|-------|--------|------|-----|-----|
| FL_Window | 0 | 7 | 1 | 0 | % | 0 | 100 |
| FR_Window | 7 | 7 | 1 | 0 | % | 0 | 100 |
| RL_Window | 14 | 7 | 1 | 0 | % | 0 | 100 |
| RR_Window | 21 | 7 | 1 | 0 | % | 0 | 100 |

### Diagnostic Trouble Codes (DTCs)

| DTC | Description | Severity |
|-----|-------------|----------|
| BDC_DOOR_0_BLOCKED | Front left door obstruction | Warning |
| BDC_DOOR_1_BLOCKED | Front right door obstruction | Warning |
| BDC_DOOR_2_BLOCKED | Rear left door obstruction | Warning |
| BDC_DOOR_3_BLOCKED | Rear right door obstruction | Warning |
| BDC_DOOR_0_FAULT | Front left door ECU fault | Error |

---

## Pinch Protection

The door ECU implements pinch protection per ISO 12237:

### Detection Method
- Current monitoring during closure
- Obstruction threshold: 50mA deviation from expected profile
- Reversal distance: 50mm
- Sensitivity levels: 1-10 (default: 5)

### Response
- Immediate stop on detection
- Reverse direction
- Set BLOCKED state
- Log DTC

---

## Child Lock

### Configuration
- Available on rear doors (RL, RR)
- Prevents interior door handle operation
- Exterior handle still functional
- Controlled via diagnostic service

---

## Window Control

### Features
- Individual control per door
- Auto-up/auto-down with pinch protection
- Global lock/disable via dashboard
- Position memory per door

### Timing
- Full travel: 4.0 seconds
- Step resolution: 10%
- Anti-trap sensitivity: Same as doors
