"""
Robot Framework Library for CAN Communication

This library provides keywords for interacting with virtual CAN bus
in Robot Framework tests.
"""

import logging
import time
from typing import Optional, List
from robot.api.deco import keyword, library

logger = logging.getLogger(__name__)


@library
class CANLibrary:
    """
    Robot Framework library for CAN communication.

    Provides keywords for:
    - Sending CAN messages
    - Receiving and verifying CAN messages
    - CAN bus monitoring
    - Message logging
    """

    ROBOT_LIBRARY_SCOPE = "SUITE"
    ROBOT_LIBRARY_VERSION = "0.1.0"

    # Standard CAN IDs
    BMS_STATUS_ID = 0x100
    BMS_CELL_DATA_ID = 0x101
    BMS_FAULT_ID = 0x102
    BDC_STATUS_ID = 0x200
    BDC_DOOR_POS_ID = 0x201
    BDC_LOCK_STATUS_ID = 0x202

    def __init__(self):
        """Initialize the CAN Library"""
        self._can_interface = None
        self._received_messages = []
        self._channel = "virtual0"

    @keyword
    def start_can_interface(self, channel: str = "virtual0", bitrate: int = 500000):
        """
        Start the CAN interface

        Arguments:
            channel: CAN channel name
            bitrate: Bus speed in bps

        Example:
            | Start CAN Interface | channel=virtual0 | bitrate=500000 |
        """
        from ecu_simulation.can_interface import CANInterface

        self._can_interface = CANInterface(channel=channel, bitrate=bitrate)
        self._channel = channel
        self._received_messages = []

        # Register wildcard callback to capture all messages
        self._can_interface.add_callback(0xFFFFFFFF, self._message_callback)

        logger.info(f"Started CAN interface on {channel} at {bitrate} bps")

    def _message_callback(self, message):
        """Internal callback for received messages"""
        self._received_messages.append(message)

    @keyword
    def stop_can_interface(self):
        """Stop the CAN interface

        Example:
            | Stop CAN Interface |
        """
        self._can_interface = None
        self._received_messages = []
        logger.info("Stopped CAN interface")

    @keyword
    def send_can_message(self, can_id: int, data: str, extended: bool = False) -> bool:
        """
        Send a CAN message

        Arguments:
            can_id: CAN message ID (decimal or hex)
            data: Message data as hex string
            extended: Use extended addressing (29-bit)

        Returns:
            True if message sent successfully

        Example:
            | Send CAN Message | can_id=0x100 | data=01A20405060708 |
            | Send CAN Message | can_id=256 | data=01A20405060708 | extended=True |
        """
        import asyncio

        if self._can_interface is None:
            raise RuntimeError("CAN interface not started")

        # Convert hex string to bytes
        data_bytes = bytes.fromhex(data)

        # Send message
        loop = asyncio.get_event_loop()
        success = loop.run_until_complete(self._can_interface.send(can_id, data_bytes, extended))

        logger.info(f"Sent CAN message: ID=0x{can_id:03X}, Data={data}")
        return success

    @keyword
    def send_bms_status(
        self, soc: float, voltage: float, current: float, temperature: float
    ) -> bool:
        """
        Send a BMS status message

        Arguments:
            soc: State of charge (0-100%)
            voltage: Pack voltage (V)
            current: Pack current (A)
            temperature: Pack temperature (°C)

        Returns:
            True if message sent successfully

        Example:
            | Send BMS Status | soc=85.5 | voltage=400.0 | current=10.0 | temperature=25.0 |
        """
        if self._can_interface is None:
            raise RuntimeError("CAN interface not started")

        import asyncio

        data = self._can_interface.build_bms_status(soc, voltage, current, temperature)
        loop = asyncio.get_event_loop()
        return loop.run_until_complete(self._can_interface.send(self.BMS_STATUS_ID, data))

    @keyword
    def send_door_status(
        self,
        fl_open: bool = False,
        fr_open: bool = False,
        rl_open: bool = False,
        rr_open: bool = False,
        fl_locked: bool = True,
        fr_locked: bool = True,
        rl_locked: bool = True,
        rr_locked: bool = True,
    ) -> bool:
        """
        Send a door status message

        Arguments:
            fl_open: Front left open
            fr_open: Front right open
            rl_open: Rear left open
            rr_open: Rear right open
            fl_locked: Front left locked
            fr_locked: Front right locked
            rl_locked: Rear left locked
            rr_locked: Rear right locked

        Returns:
            True if message sent successfully

        Example:
            | Send Door Status | fl_open=${True} | fl_locked=${False} |
        """
        if self._can_interface is None:
            raise RuntimeError("CAN interface not started")

        import asyncio

        doors = {
            "fl_open": fl_open,
            "fr_open": fr_open,
            "rl_open": rl_open,
            "rr_open": rr_open,
            "fl_locked": fl_locked,
            "fr_locked": fr_locked,
            "rl_locked": rl_locked,
            "rr_locked": rr_locked,
        }
        data = self._can_interface.build_door_status(doors)
        loop = asyncio.get_event_loop()
        return loop.run_until_complete(self._can_interface.send(self.BDC_STATUS_ID, data))

    @keyword
    def wait_for_can_message(self, can_id: int, timeout: float = 5.0) -> bool:
        """
        Wait for a specific CAN message

        Arguments:
            can_id: CAN message ID to wait for
            timeout: Maximum wait time in seconds

        Returns:
            True if message received, False if timeout

        Example:
            | ${received}= | Wait For CAN Message | can_id=0x100 | timeout=5 |
        """
        start_time = time.time()
        while time.time() - start_time < timeout:
            for msg in self._received_messages:
                if msg.id == can_id:
                    return True
            time.sleep(0.05)
        return False

    @keyword
    def get_last_can_message(self, can_id: Optional[int] = None) -> dict:
        """
        Get the last received CAN message

        Arguments:
            can_id: Optional CAN ID filter

        Returns:
            Dictionary with message data (id, data, timestamp, dlc)

        Example:
            | ${msg}= | Get Last CAN Message | can_id=0x100 |
            | Log | Received: ${msg['data']} |
        """
        if not self._received_messages:
            return {}

        messages = self._received_messages
        if can_id is not None:
            messages = [m for m in messages if m.id == can_id]

        if not messages:
            return {}

        msg = messages[-1]
        return {
            "id": msg.id,
            "data": msg.data.hex(),
            "timestamp": msg.timestamp,
            "dlc": msg.dlc,
        }

    @keyword
    def get_can_message_count(self, can_id: Optional[int] = None) -> int:
        """
        Get count of received CAN messages

        Arguments:
            can_id: Optional CAN ID filter

        Returns:
            Number of messages received

        Example:
            | ${count}= | Get CAN Message Count | can_id=0x100 |
        """
        if can_id is None:
            return len(self._received_messages)
        return len([m for m in self._received_messages if m.id == can_id])

    @keyword
    def clear_can_messages(self):
        """Clear the received message buffer

        Example:
            | Clear CAN Messages |
        """
        self._received_messages = []
        logger.info("Cleared CAN message buffer")

    @keyword
    def get_can_bus_load(self) -> float:
        """
        Get current CAN bus load percentage

        Returns:
            Bus load (0-100%)

        Example:
            | ${load}= | Get CAN Bus Load |
            | Should Be True | ${load} < 50 |
        """
        if self._can_interface is None:
            raise RuntimeError("CAN interface not started")
        return self._can_interface.get_bus_load()

    @keyword
    def verify_can_data(self, can_id: int, expected_data: str, mask: Optional[str] = None) -> bool:
        """
        Verify CAN message data

        Arguments:
            can_id: CAN message ID
            expected_data: Expected data as hex string
            mask: Optional mask for partial matching (X = ignore)

        Returns:
            True if data matches

        Example:
            | ${result}= | Verify CAN Data | can_id=0x100 | expected_data=01A2XXXX |
        """
        msg = self.get_last_can_message(can_id)
        if not msg:
            return False

        actual = msg["data"].upper()
        expected = expected_data.upper()

        if mask is None:
            return actual == expected

        # Apply mask
        for i in range(len(expected)):
            if i >= len(actual):
                return False
            if expected[i] != "X" and expected[i] != actual[i]:
                return False
        return True

    @keyword
    def get_can_statistics(self) -> dict:
        """
        Get CAN interface statistics

        Returns:
            Dictionary with tx_count, rx_count, bus_load, channel, bitrate

        Example:
            | ${stats}= | Get CAN Statistics |
            | Log | TX: ${stats['tx_count']}, RX: ${stats['rx_count']} |
        """
        if self._can_interface is None:
            raise RuntimeError("CAN interface not started")
        return self._can_interface.get_statistics()


if __name__ == "__main__":
    # Test the library
    can = CANLibrary()

    print("Testing CAN Library...")
    can.start_can_interface()

    # Send a message
    can.send_can_message(0x100, "01A20405060708")
    print(f"Message count: {can.get_can_message_count()}")

    # Get last message
    msg = can.get_last_can_message(0x100)
    print(f"Last message: {msg}")

    can.stop_can_interface()
    print("CAN Library test complete")
