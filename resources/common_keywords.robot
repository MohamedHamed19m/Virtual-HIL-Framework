*** Settings ***
Documentation     Common keywords and setup for all test suites
...               This file contains reusable keywords used across multiple test suites.

Library           Collections
Library           DateTime


*** Variables ***
# Test timeouts
${DEFAULT_TIMEOUT}       10s
${LONG_TIMEOUT}          60s
${SHORT_TIMEOUT}         5s

# Retry settings
${MAX_RETRIES}           3
${RETRY_DELAY}           1s


*** Keywords ***
Log Test Start
    [Documentation]    Log test start information
    [Arguments]    ${test_name}
    ${timestamp}=    Get Current Date    result_format=%Y-%m-%d %H:%M:%S
    Log    \n=================================================================\n
    Log    Starting test: ${test_name}
    Log    Timestamp: ${timestamp}
    Log    \n=================================================================\n    console=True

Log Test End
    [Documentation]    Log test end information
    [Arguments]    ${test_name}    ${status}=PASS
    ${timestamp}=    Get Current Date    result_format=%Y-%m-%d %H:%M:%S
    Log    \n=================================================================\n
    Log    Test ${status}: ${test_name}
    Log    Timestamp: ${timestamp}
    Log    \n=================================================================\n    console=True

Wait For Condition
    [Documentation]    Wait for a condition to become true
    ...                Returns True if condition met, False if timeout
    [Arguments]    ${condition}    ${timeout}=${DEFAULT_TIMEOUT}    ${poll_interval}=0.5s

    ${start_time}=    Get Time    epoch
    ${timeout_sec}=    Convert Time    ${timeout}    result_format=number

    FOR    ${i}    IN RANGE    1000
        ${result}=    Evaluate    ${condition}
        Return From Keyword If    ${result}    ${True}

        ${current_time}=    Get Time    epoch
        ${elapsed}=    Evaluate    ${current_time} - ${start_time}
        Return From Keyword If    ${elapsed} > ${timeout_sec}    ${False}

        Sleep    ${poll_interval}
    END

    RETURN    ${False}

Retry Keyword
    [Documentation]    Retry a keyword up to MAX_RETRIES times
    [Arguments]    ${keyword}    @{args}

    FOR    ${i}    IN RANGE    ${MAX_RETRIES}
        ${status}=    Run Keyword And Return Status    ${keyword}    @{args}
        Return From Keyword If    ${status}    ${True}
        Log    Retry ${i+1}/${MAX_RETRIES} for ${keyword}
        Sleep    ${RETRY_DELAY}
    END

    Fail    Keyword '${keyword}' failed after ${MAX_RETRIES} retries

Safe Run Keyword
    [Documentation]    Run keyword and continue even if it fails
    [Arguments]    ${keyword}    @{args}

    ${status}=    Run Keyword And Return Status    ${keyword}    @{args}
    Log    Keyword '${keyword}' ${status}    console=True

    RETURN    ${status}

Verify Value In Range
    [Documentation]    Verify a value is within specified range
    [Arguments]    ${value}    ${min}    ${max}    ${msg}=${EMPTY}

    ${result}=    Evaluate    ${min} <= ${value} <= ${max}

    ${default_msg}=    Set Variable If    ${msg}==${EMPTY}
    ...    Value ${value} not in range [${min}, ${max}]
    ...    ${msg}

    Should Be True    ${result}    msg=${default_msg}

Verify List Contains
    [Documentation]    Verify a list contains all expected values
    [Arguments]    ${list}    @{expected}

    FOR    ${item}    IN    @{expected}
        List Should Contain Value    ${list}    ${item}
    END

Get Dictionary Value
    [Documentation]    Get value from dictionary with default
    [Arguments]    &{dict}    ${key}    ${default}=${None}

    ${has_key}=    Dictionary Should Contain Key    ${dict}    ${key}    limit=False
    ${value}=    Set Variable If    ${has_key}    ${dict}[${key}]    ${default}

    RETURN    ${value}

Compare Dictionaries
    [Documentation]    Compare two dictionaries, ignore keys with None values
    [Arguments]    &{dict1}    &{dict2}

    ${keys1}=    Get Dictionary Keys    ${dict1}
    ${keys2}=    Get Dictionary Keys    ${dict2}

    Lists Should Be Equal    ${keys1}    ${keys2}    msg=Dictionaries have different keys

    FOR    ${key}    IN    @{keys1}
        ${val1}=    Get From Dictionary    ${dict1}    ${key}
        ${val2}=    Get From Dictionary    ${dict2}    ${key}

        Continue If    ${val1} == ${None}
        Continue If    ${val2} == ${None}

        Should Be Equal    ${val1}    ${val2}    msg=Values differ for key '${key}'
    END

Format CAN ID
    [Documentation]    Format CAN ID as hex string
    [Arguments]    ${can_id}    ${prefix}=0x

    ${hex_id}=    Convert To Hex    ${can_id}    prefix=${prefix}    length=3
    RETURN    ${hex_id}

Parse CAN Message
    [Documentation]    Parse CAN message data into bytes
    [Arguments]    ${hex_data}

    @{bytes}=    Create List
    ${length}=    Get Length    ${hex_data}

    FOR    ${i}    IN RANGE    0    ${length}    2
        ${byte_str}=    Get Substring    ${hex_data}    ${i}    ${i+2}
        ${byte}=    Convert To Integer    ${byte_str}    base=16
        Append To List    ${bytes}    ${byte}
    END

    RETURN    @{bytes}

Log CAN Message
    [Documentation]    Log CAN message details
    [Arguments]    ${can_id}    ${data}    ${direction}=RX

    ${formatted_id}=    Format CAN ID    ${can_id}
    Log    CAN ${direction}: ID=${formatted_id} Data=${data}    console=True

Calculate Percentage
    [Documentation]    Calculate percentage
    [Arguments]    ${value}    ${total}

    ${percentage}=    Evaluate    (${value} / ${total}) * 100 if ${total} != 0 else 0
    RETURN    ${percentage}

Average List
    [Documentation]    Calculate average of list values
    [Arguments]    @{values}

    ${sum}=    Evaluate    sum(${values})
    ${count}=    Get Length    ${values}
    ${average}=    Evaluate    ${sum} / ${count} if ${count} > 0 else 0

    RETURN    ${average}

Max List
    [Documentation]    Get maximum value from list
    [Arguments]    @{values}

    ${max}=    Evaluate    max(${values}) if len(${values}) > 0 else None
    RETURN    ${max}

Min List
    [Documentation]    Get minimum value from list
    [Arguments]    @{values}

    ${min}=    Evaluate    min(${values}) if len(${values}) > 0 else None
    RETURN    ${min}

Convert Celsius To Fahrenheit
    [Documentation]    Convert temperature from C to F
    [Arguments]    ${celsius}

    ${fahrenheit}=    Evaluate    (${celsius} * 9/5) + 32
    RETURN    ${fahrenheit}

Convert Fahrenheit To Celsius
    [Documentation]    Convert temperature from F to C
    [Arguments]    ${fahrenheit}

    ${celsius}=    Evaluate    (${fahrenheit} - 32) * 5/9
    RETURN    ${celsius}

Sleep Milliseconds
    [Documentation]    Sleep for specified milliseconds
    [Arguments]    ${ms}

    ${seconds}=    Evaluate    ${ms} / 1000.0
    Sleep    ${seconds}

Create Timestamp
    [Documentation]    Create formatted timestamp string
    [Arguments]    ${format}=%Y%m%d_%H%M%S

    ${timestamp}=    Get Current Date    result_format=${format}
    RETURN    ${timestamp}
