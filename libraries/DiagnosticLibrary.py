"""
Robot Framework Library for UDS Diagnostics

This library provides keywords for UDS diagnostic communication
in Robot Framework tests.
"""

import logging
from typing import Optional, List
from robot.api.deco import keyword, library

logger = logging.getLogger(__name__)


@library
class DiagnosticLibrary:
    """
    Robot Framework library for UDS diagnostics.

    Provides keywords for:
    - UDS session control
    - Reading/writing data identifiers
    - DTC handling
    - Security access
    - Routine execution
    """

    ROBOT_LIBRARY_SCOPE = "SUITE"
    ROBOT_LIBRARY_VERSION = "0.1.0"

    # UDS Service IDs
    SID_SESSION_CONTROL = 0x10
    SID_READ_DID = 0x22
    SID_WRITE_DID = 0x2E
    SID_READ_DTC = 0x19
    SID_CLEAR_DTC = 0x14
    SID_SECURITY_ACCESS = 0x27
    SID_ROUTINE_CONTROL = 0x31
    SID_TESTER_PRESENT = 0x3E
    SID_DTC_SETTING = 0x85

    # Session types
    SESSION_DEFAULT = 0x01
    SESSION_PROGRAMMING = 0x02
    SESSION_EXTENDED = 0x03
    SESSION_SAFETY = 0x04

    # Standard DIDs
    DID_ECU_SERIAL = 0xF10C
    DID_HARDWARE_NUMBER = 0xF187
    DID_SOFTWARE_VERSION = 0xF19E
    DID_SUPPLIER = 0xF198

    def __init__(self):
        """Initialize the Diagnostic Library"""
        self._diag_server = None
        self._current_session = self.SESSION_DEFAULT

    @keyword
    def start_diagnostic_session(self, ecu_name: str = "VirtualECU"):
        """
        Start a diagnostic session with an ECU

        Arguments:
            ecu_name: Name of the ECU to connect to

        Example:
            | Start Diagnostic Session | ecu_name=VirtualECU |
        """
        from ecu_simulation.diagnostic_server import DiagnosticServer

        self._diag_server = DiagnosticServer(ecu_name=ecu_name)
        self._current_session = self.SESSION_DEFAULT

        import asyncio

        loop = asyncio.get_event_loop()
        loop.run_until_complete(self._diag_server.start())

        logger.info(f"Started diagnostic session with {ecu_name}")

    @keyword
    def stop_diagnostic_session(self):
        """Stop the current diagnostic session

        Example:
            | Stop Diagnostic Session |
        """
        if self._diag_server:
            import asyncio

            loop = asyncio.get_event_loop()
            loop.run_until_complete(self._diag_server.stop())
            self._diag_server = None
        logger.info("Stopped diagnostic session")

    @keyword
    def set_diagnostic_session(self, session_type: int) -> bool:
        """
        Change diagnostic session type

        Arguments:
            session_type: Session type (1=Default, 2=Programming, 3=Extended, 4=Safety)

        Returns:
            True if session changed successfully

        Example:
            | Set Diagnostic Session | ${3} | # Extended session |
        """
        if self._diag_server is None:
            raise RuntimeError("Diagnostic session not started")

        import asyncio

        request = bytes([self.SID_SESSION_CONTROL, session_type])
        loop = asyncio.get_event_loop()
        response = loop.run_until_complete(self._diag_server.process_request(request))

        if not response.is_negative:
            self._current_session = session_type
            logger.info(f"Changed to session type {session_type}")
            return True
        return False

    @keyword
    def read_data_identifier(self, did: int) -> Optional[bytes]:
        """
        Read a data identifier

        Arguments:
            did: Data identifier to read

        Returns:
            Data value or None if failed

        Example:
            | ${data}= | Read Data Identifier | did=0xF19E |
            | Log | Software version: ${data} |
        """
        if self._diag_server is None:
            raise RuntimeError("Diagnostic session not started")

        import asyncio

        request = bytes([self.SID_READ_DID, (did >> 8) & 0xFF, did & 0xFF])
        loop = asyncio.get_event_loop()
        response = loop.run_until_complete(self._diag_server.process_request(request))

        if response.is_negative:
            logger.error(f"Failed to read DID 0x{did:04X}: NRC=0x{response.nrc:02X}")
            return None

        # Extract data (skip DID in response)
        return response.data[2:] if len(response.data) > 2 else response.data

    @keyword
    def write_data_identifier(self, did: int, data: bytes) -> bool:
        """
        Write a data identifier

        Arguments:
            did: Data identifier to write
            data: Data to write

        Returns:
            True if write successful

        Example:
            | Write Data Identifier | did=0xF123 | data=01020304 |
        """
        if self._diag_server is None:
            raise RuntimeError("Diagnostic session not started")

        import asyncio

        request = bytes([self.SID_WRITE_DID, (did >> 8) & 0xFF, did & 0xFF]) + data
        loop = asyncio.get_event_loop()
        response = loop.run_until_complete(self._diag_server.process_request(request))

        if response.is_negative:
            logger.error(f"Failed to write DID 0x{did:04X}: NRC=0x{response.nrc:02X}")
            return False

        logger.info(f"Wrote DID 0x{did:04X}: {data.hex()}")
        return True

    @keyword
    def read_ecu_serial_number(self) -> Optional[str]:
        """
        Read ECU serial number

        Returns:
            Serial number string or None

        Example:
            | ${serial}= | Read ECU Serial Number |
        """
        data = self.read_data_identifier(self.DID_ECU_SERIAL)
        return data.decode("utf-8", errors="ignore") if data else None

    @keyword
    def read_software_version(self) -> Optional[str]:
        """
        Read ECU software version

        Returns:
            Software version string or None

        Example:
            | ${version}= | Read Software Version |
        """
        data = self.read_data_identifier(self.DID_SOFTWARE_VERSION)
        return data.decode("utf-8", errors="ignore") if data else None

    @keyword
    def read_dtcs(self) -> List[dict]:
        """
        Read all stored Diagnostic Trouble Codes

        Returns:
            List of DTC dictionaries with code and status

        Example:
            | ${dtcs}= | Read DTCs |
            | FOR | ${dtc} | IN | @{dtcs} |
            | | Log | DTC: ${dtc['code']} |
            | END |
        """
        if self._diag_server is None:
            raise RuntimeError("Diagnostic session not started")

        return [
            {"code": dtc.code, "status": dtc.status} for dtc in self._diag_server.get_all_dtcs()
        ]

    @keyword
    def clear_dtcs(self) -> bool:
        """
        Clear all stored DTCs

        Returns:
            True if cleared successfully

        Example:
            | Clear DTCs |
        """
        if self._diag_server is None:
            raise RuntimeError("Diagnostic session not started")

        import asyncio

        request = bytes([self.SID_CLEAR_DTC, 0xFF, 0xFF])  # Clear all
        loop = asyncio.get_event_loop()
        response = loop.run_until_complete(self._diag_server.process_request(request))

        if response.is_negative:
            logger.error(f"Failed to clear DTCs: NRC=0x{response.nrc:02X}")
            return False

        logger.info("Cleared all DTCs")
        return True

    @keyword
    def store_dtc(self, code: str, status: int = 0x01):
        """
        Store a DTC (for testing purposes)

        Arguments:
            code: DTC code (e.g., "P0171")
            status: Status byte

        Example:
            | Store DTC | code=P0171 | status=0x01 |
        """
        if self._diag_server is None:
            raise RuntimeError("Diagnostic session not started")

        self._diag_server.store_dtc(code, status)
        logger.info(f"Stored DTC: {code}")

    @keyword
    def verify_dtc_exists(self, code: str) -> bool:
        """
        Verify a specific DTC exists

        Arguments:
            code: DTC code to check

        Returns:
            True if DTC exists

        Example:
            | ${exists}= | Verify DTC Exists | code=P0171 |
            | Should Be True | ${exists} |
        """
        if self._diag_server is None:
            raise RuntimeError("Diagnostic session not started")

        return code in self._diag_server.dtcs

    @keyword
    def security_access_request_seed(self, level: int = 1) -> Optional[bytes]:
        """
        Request security access seed

        Arguments:
            level: Security level (odd number = request seed)

        Returns:
            Seed or None if failed

        Example:
            | ${seed}= | Security Access Request Seed | level=1 |
        """
        if self._diag_server is None:
            raise RuntimeError("Diagnostic session not started")

        import asyncio

        sub_function = level * 2 - 1  # Odd for seed request
        request = bytes([self.SID_SECURITY_ACCESS, sub_function])
        loop = asyncio.get_event_loop()
        response = loop.run_until_complete(self._diag_server.process_request(request))

        if response.is_negative:
            logger.error(f"Security access denied: NRC=0x{response.nrc:02X}")
            return None

        return response.data[1:] if len(response.data) > 1 else response.data

    @keyword
    def security_access_send_key(self, level: int = 1, key: bytes = b"\x01\x02\x03\x04") -> bool:
        """
        Send security access key

        Arguments:
            level: Security level (even number = send key)
            key: Key bytes

        Returns:
            True if access granted

        Example:
            | ${result}= | Security Access Send Key | level=2 | key=01020304 |
        """
        if self._diag_server is None:
            raise RuntimeError("Diagnostic session not started")

        import asyncio

        sub_function = level * 2  # Even for send key
        request = bytes([self.SID_SECURITY_ACCESS, sub_function]) + key
        loop = asyncio.get_event_loop()
        response = loop.run_until_complete(self._diag_server.process_request(request))

        if response.is_negative:
            logger.error(f"Security access denied: NRC=0x{response.nrc:02X}")
            return False

        logger.info(f"Security access granted for level {level}")
        return True

    @keyword
    def routine_control(self, routine_id: int, control_type: int = 0x01, data: bytes = b"") -> bool:
        """
        Execute a diagnostic routine

        Arguments:
            routine_id: Routine identifier
            control_type: Control type (1=Start, 2=Stop, 3=Request Results)
            data: Optional routine parameters

        Returns:
            True if routine executed successfully

        Example:
            | Routine Control | routine_id=0x0201 | control_type=0x01 |
        """
        if self._diag_server is None:
            raise RuntimeError("Diagnostic session not started")

        import asyncio

        request = (
            bytes(
                [
                    self.SID_ROUTINE_CONTROL,
                    control_type,
                    (routine_id >> 8) & 0xFF,
                    routine_id & 0xFF,
                ]
            )
            + data
        )
        loop = asyncio.get_event_loop()
        response = loop.run_until_complete(self._diag_server.process_request(request))

        return not response.is_negative

    @keyword
    def tester_present(self, suppress_response: bool = False) -> bool:
        """
        Send Tester Present message

        Arguments:
            suppress_response: Suppress positive response

        Returns:
            True if successful

        Example:
            | Tester Present |
        """
        if self._diag_server is None:
            raise RuntimeError("Diagnostic session not started")

        import asyncio

        sub_function = 0x80 if suppress_response else 0x00
        request = bytes([self.SID_TESTER_PRESENT, sub_function])
        loop = asyncio.get_event_loop()
        response = loop.run_until_complete(self._diag_server.process_request(request))

        return not response.is_negative

    @keyword
    def enable_dtc_setting(self, enable: bool = True) -> bool:
        """
        Enable or disable DTC setting

        Arguments:
            enable: True to enable, False to disable

        Returns:
            True if successful

        Example:
            | Enable DTC Setting | enable=${True} |
        """
        if self._diag_server is None:
            raise RuntimeError("Diagnostic session not started")

        import asyncio

        request = bytes([self.SID_DTC_SETTING, 0x01 if enable else 0x00])
        loop = asyncio.get_event_loop()
        response = loop.run_until_complete(self._diag_server.process_request(request))

        return not response.is_negative


if __name__ == "__main__":
    # Test the library
    diag = DiagnosticLibrary()

    print("Testing Diagnostic Library...")
    diag.start_diagnostic_session()

    # Read ECU info
    serial = diag.read_ecu_serial_number()
    print(f"ECU Serial: {serial}")

    version = diag.read_software_version()
    print(f"Software Version: {version}")

    # Test DTCs
    diag.store_dtc("P0171")
    dtcs = diag.read_dtcs()
    print(f"DTCs: {dtcs}")

    # Verify DTC
    print(f"DTC exists: {diag.verify_dtc_exists('P0171')}")

    diag.stop_diagnostic_session()
    print("Diagnostic Library test complete")
