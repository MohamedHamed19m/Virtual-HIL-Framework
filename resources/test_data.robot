*** Settings ***
Documentation     Test data fixtures and data generators
...               This file provides test data for various test scenarios.


*** Variables ***
# =============================================================================
# Charging Profile Data
# =============================================================================

# Constant current charging profiles
&{CC_CHARGE_PROFILE}    current=10    duration=3600    expected_soc_increase=11.7
&{FAST_CHARGE_PROFILE}  current=25    duration=3600    expected_soc_increase=29.3
&{SLOW_CHARGE_PROFILE}  current=5     duration=3600    expected_soc_increase=5.8

# Discharge profiles
&{NORMAL_DISCHARGE}     current=-20   duration=1800    expected_soc_decrease=11.7
&{HIGH_DISCHARGE}       current=-50   duration=600     expected_soc_decrease=14.6

# =============================================================================
# Cell Imbalance Test Data
# =============================================================================

# Cell imbalance scenarios
&{IMBALANCE_SCENARIO_1}
...    description=Minor imbalance
...    cell_0_voltage=3.75
...    cell_1_voltage=3.65
...    expected_balance_time=5

&{IMBALANCE_SCENARIO_2}
...    description=Significant imbalance
...    cell_0_voltage=4.0
...    cell_1_voltage=3.4
...    expected_balance_time=15

&{IMBALANCE_SCENARIO_3}
...    description=Severe imbalance
...    cell_0_voltage=4.15
...    cell_1_voltage=3.3
...    expected_balance_time=30

# =============================================================================
# Temperature Test Data
# =============================================================================

# Temperature test points
@{TEMPERATURE_TEST_POINTS}    -20    -10    0    10    20    25    30    40    50    60

# Thermal gradient scenarios
&{THERMAL_GRADIENT_1}
...    description=Normal gradient
...    temp_min=20
...    temp_max=30
...    temp_spread=10

&{THERMAL_GRADIENT_2}
...    description=High gradient
...    temp_min=15
...    temp_max=45
...    temp_spread=30

&{THERMAL_GRADIENT_3}
...    description=Critical gradient
...    temp_min=10
...    temp_max=55
...    temp_spread=45

# =============================================================================
# Door Test Data
# =============================================================================

# Door position test scenarios
&{DOOR_FULL_OPEN}        target_percentage=100    expected_time=2.0
&{DOOR_HALF_OPEN}        target_percentage=50     expected_time=1.0
&{DOOR_CRACK_OPEN}       target_percentage=10     expected_time=0.3

# Door lock test sequences
@{LOCK_TEST_SEQUENCE}    lock    verify_locked    unlock    verify_unlocked

# Window test positions
@{WINDOW_TEST_POSITIONS} 0    25    50    75    100

# =============================================================================
# Fault Test Data
# =============================================================================

# Single fault scenarios
&{FAULT_OVERVOLTAGE}
...    fault_type=OVERVOLTAGE
...    injection_method=set_cell_voltage
...    cell_id=0
...    voltage=4.3
...    expected_dtc=BMS_OVERVOLTAGE_ACTIVE

&{FAULT_UNDERVOLTAGE}
...    fault_type=UNDERVOLTAGE
...    injection_method=set_cell_voltage
...    cell_id=0
...    voltage=2.5
...    expected_dtc=BMS_UNDERVOLTAGE_ACTIVE

&{FAULT_OVERTEMP}
...    fault_type=OVERTEMPERATURE
...    injection_method=set_cell_temperature
...    cell_id=0
...    temperature=70
...    expected_dtc=BMS_OVERTEMPERATURE_ACTIVE

&{FAULT_UNDERTEMP}
...    fault_type=UNDERTEMPERATURE
...    injection_method=set_cell_temperature
...    cell_id=0
...    temperature=-25
...    expected_dtc=BMS_UNDERTEMPERATURE_ACTIVE

# Multiple fault scenarios
@{MULTIPLE_FAULTS_SEQUENCE}
...    OVERVOLTAGE
...    OVERTEMPERATURE
...    UNDERVOLTAGE
...    FAULT_DOOR_BLOCK

# =============================================================================
# CAN Message Test Data
# =============================================================================#

# Standard CAN test messages
&{CAN_BMS_STATUS_MSG}
...    can_id=0x100
...    data=AB06018608D81900
...    description=BMS Status message

&{CAN_DOOR_STATUS_MSG}
...    can_id=0x200
...    data=0000FFFF
...    description=Door Status message (all closed, locked)

&{CAN_BMS_FAULT_MSG}
...    can_id=0x102
...    data=01
...    description=BMS Fault indication

# CAN stress test data
@{CAN_STRESS_IDS}    0x100    0x101    0x102    0x200    0x201    0x202

# =============================================================================
# Diagnostic Test Data
# =============================================================================#

# Test DIDs
&{DID_READ_TEST}
...    did=0xF19E
...    expected_data_type=string
...    description=Software version DID

&{DID_WRITE_TEST}
...    did=0xF123
...    test_data=01020304
...    description=Test write DID

# DTC test codes
@{TEST_DTC_CODES}    P0171    P0300    P0420    P0700    B0001    C0020    U0100

# Security access test levels
@{SECURITY_LEVELS}    1    2    3    4

# =============================================================================
# Performance Test Data
# =============================================================================#

# Response time thresholds
&{PERFORMANCE_THRESHOLDS}
...    max_state_query_time=100
...    max_can_tx_time=10
...    max_diag_response_time=500
...    max_balance_cycle_time=100

# Stress test parameters
&{STRESS_TEST_PARAMS}
...    num_iterations=1000
...    concurrent_operations=10
...    duration_seconds=300

# =============================================================================
# Boundary Value Test Data
# =============================================================================#

# SOC boundary values
@{SOC_BOUNDARIES}    0    0.1    10    50    90    99.9    100

# Voltage boundary values
@{VOLTAGE_BOUNDARIES}    2.8    3.0    3.7    4.2    4.3

# Temperature boundary values
@{TEMP_BOUNDARIES}    -20    -10    25    45    61


*** Keywords ***
Get Charging Profile
    [Documentation]    Get charging profile by name
    [Arguments]    ${profile_name}

    ${profile}=    Get From Dictionary    ${CC_CHARGE_PROFILE}    ${profile_name}
    [Return]    ${profile}

Get Imbalance Scenario
    [Documentation]    Get imbalance scenario by number
    [Arguments]    ${scenario_num}

    ${scenario_name}=    Set Variable If    ${scenario_num}==1    IMBALANCE_SCENARIO_1
    ...    ${scenario_num}==2    IMBALANCE_SCENARIO_2
    ...    IMBALANCE_SCENARIO_3

    ${scenario}=    Get From Dictionary    &{IMBALANCE_SCENARIO_1}    ${scenario_name}
    [Return]    ${scenario}

Get Fault Scenario
    [Documentation]    Get fault scenario by type
    [Arguments]    ${fault_type}

    Run Keyword If    '${fault_type}'=='OVERVOLTAGE'    [Return]    &{FAULT_OVERVOLTAGE}
    Run Keyword If    '${fault_type}'=='UNDERVOLTAGE'   [Return]    &{FAULT_UNDERVOLTAGE}
    Run Keyword If    '${fault_type}'=='OVERTEMPERATURE'    [Return]    &{FAULT_OVERTEMP}
    Run Keyword If    '${fault_type}'=='UNDERTEMPERATURE'    [Return]    &{FAULT_UNDERTEMP}

    [Return]    ${None}

Generate Random SOC
    [Documentation]    Generate random SOC within valid range
    [Arguments]    ${min}=${TEST_SOC_MIN}    ${max}=${TEST_SOC_MAX}

    ${soc}=    Evaluate    random.uniform(${min}, ${max})    modules=random
    ${soc_rounded}=    Evaluate    round(${soc}, 1)
    [Return]    ${soc_rounded}

Generate Random Voltage
    [Documentation]    Generate random cell voltage within valid range
    [Arguments]    ${min}=${TEST_VOLTAGE_MIN}    ${max}=${TEST_VOLTAGE_MAX}

    ${voltage}=    Evaluate    random.uniform(${min}, ${max})    modules=random
    ${voltage_rounded}=    Evaluate    round(${voltage}, 3)
    [Return]    ${voltage_rounded}

Generate Random Temperature
    [Documentation]    Generate random temperature within valid range
    [Arguments]    ${min}=${TEST_TEMP_MIN}    ${max}=${TEST_TEMP_MAX}

    ${temp}=    Evaluate    random.uniform(${min}, ${max})    modules=random
    ${temp_rounded}=    Evaluate    round(${temp}, 1)
    [Return]    ${temp_rounded}

Create Cell Voltage List
    [Documentation]    Create list of cell voltages with optional variation
    [Arguments]    ${num_cells}=${NUM_CELLS}    ${base_voltage}=3.7    ${variation}=0.1

    @{voltages}=    Create List
    FOR    ${i}    IN RANGE    ${num_cells}
        ${voltage}=    Evaluate    ${base_voltage} + random.uniform(-${variation}, ${variation})    modules=random
        ${voltage_rounded}=    Evaluate    round(${voltage}, 3)
        Append To List    ${voltages}    ${voltage_rounded}
    END

    [Return]    @{voltages}
