"""CAN Interface Simulation Module"""

import asyncio
import logging
import struct
from dataclasses import dataclass
from typing import Callable, Dict, Optional
import time

logger = logging.getLogger(__name__)


@dataclass
class CANMessage:
    """Represents a CAN message"""

    id: int
    data: bytes
    dlc: int
    timestamp: float
    extended: bool = False

    def __post_init__(self):
        if self.dlc == 0:
            self.dlc = len(self.data)


class CANInterface:
    """
    Virtual CAN bus interface for ECU communication.

    Features:
    - Message transmission and reception
    - CAN ID filtering
    - Message callback registration
    - Bus load monitoring
    - Trace recording
    """

    # Standard CAN message IDs
    BMS_STATUS_ID = 0x100
    BMS_CELL_DATA_ID = 0x101
    BMS_FAULT_ID = 0x102
    BDC_STATUS_ID = 0x200
    BDC_DOOR_POS_ID = 0x201
    BDC_LOCK_STATUS_ID = 0x202

    def __init__(self, channel: str = "virtual0", bitrate: int = 500000):
        """
        Initialize CAN interface
        Args:
            channel: CAN channel name
            bitrate: Bus speed in bps
        """
        self.channel = channel
        self.bitrate = bitrate
        self.running = False
        self.message_callbacks: Dict[int, list[Callable]] = {}
        self.message_log: list[CANMessage] = []
        self.max_log_size = 10000
        self.tx_count = 0
        self.rx_count = 0
        self.bus_load = 0.0

    def add_callback(self, can_id: int, callback: Callable[[CANMessage], None]):
        """
        Register a callback for specific CAN ID
        Args:
            can_id: CAN message ID (0xFFFFFFFF for wildcard)
            callback: Function to call when message received
        """
        if can_id not in self.message_callbacks:
            self.message_callbacks[can_id] = []
        self.message_callbacks[can_id].append(callback)

    def remove_callback(self, can_id: int, callback: Callable[[CANMessage], None]):
        """Remove a callback"""
        if can_id in self.message_callbacks and callback in self.message_callbacks[can_id]:
            self.message_callbacks[can_id].remove(callback)

    def _notify_callbacks(self, message: CANMessage):
        """Notify registered callbacks of received message"""
        # Check specific ID callbacks
        if message.id in self.message_callbacks:
            for callback in self.message_callbacks[message.id]:
                try:
                    callback(message)
                except Exception as e:
                    logger.error(f"Callback error for ID 0x{message.id:X}: {e}")

        # Check wildcard callbacks
        if 0xFFFFFFFF in self.message_callbacks:
            for callback in self.message_callbacks[0xFFFFFFFF]:
                try:
                    callback(message)
                except Exception as e:
                    logger.error(f"Wildcard callback error: {e}")

    def _log_message(self, message: CANMessage):
        """Add message to log"""
        self.message_log.append(message)
        if len(self.message_log) > self.max_log_size:
            self.message_log.pop(0)

    async def send(self, can_id: int, data: bytes, extended: bool = False) -> bool:
        """
        Send a CAN message
        Args:
            can_id: CAN message ID
            data: Message data (max 8 bytes)
            extended: Use extended addressing
        Returns:
            True if sent successfully
        """
        if len(data) > 8:
            logger.error(f"Data too long: {len(data)} bytes")
            return False

        message = CANMessage(
            id=can_id, data=data, dlc=len(data), timestamp=time.time(), extended=extended
        )

        self.tx_count += 1
        self._log_message(message)
        logger.debug(f"TX: 0x{can_id:03X} - {data.hex()}")

        # In a real implementation, this would send to physical CAN
        # For simulation, we echo back to callbacks
        self._notify_callbacks(message)

        return True

    async def receive(self, timeout: float = 1.0) -> Optional[CANMessage]:
        """
        Receive a CAN message (blocking)
        Args:
            timeout: Maximum time to wait in seconds
        Returns:
            CAN message or None if timeout
        """
        # In simulation, this would block until a message is available
        # For now, return None as we handle messages via callbacks
        await asyncio.sleep(timeout)
        return None

    def parse_bms_status(self, data: bytes) -> dict:
        """Parse BMS status message"""
        if len(data) < 8:
            return {}

        return {
            "soc": data[0] / 2.0,  # 0-100% in 0.5% steps
            "soh": data[1],  # 0-100%
            "voltage": struct.unpack("<H", data[2:4])[0] / 10.0,  # 0-65.535V
            "current": struct.unpack("<h", data[4:6])[0] / 10.0,  # Signed, +/- 3276.7A
            "temperature": data[6] - 40,  # -40 to 215 C
            "status": data[7],  # Status flags
        }

    def build_bms_status(
        self, soc: float, voltage: float, current: float, temperature: float
    ) -> bytes:
        """Build BMS status message"""
        return struct.pack(
            "<BBhhhBB",
            int(soc * 2),  # SOC
            100,  # SOH
            int(voltage * 10),  # Voltage
            int(current * 10),  # Current
            int(temperature + 40),  # Temperature
            0,  # Reserved
            0x00,  # Status
        )

    def parse_door_status(self, data: bytes) -> dict:
        """Parse door status message"""
        if len(data) < 4:
            return {}

        return {
            "fl_open": bool(data[0] & 0x01),
            "fr_open": bool(data[0] & 0x02),
            "rl_open": bool(data[0] & 0x04),
            "rr_open": bool(data[0] & 0x08),
            "fl_locked": bool(data[1] & 0x01),
            "fr_locked": bool(data[1] & 0x02),
            "rl_locked": bool(data[1] & 0x04),
            "rr_locked": bool(data[1] & 0x08),
        }

    def build_door_status(self, doors: dict) -> bytes:
        """Build door status message"""
        byte0 = 0
        byte1 = 0

        if doors.get("fl_open", False):
            byte0 |= 0x01
        if doors.get("fr_open", False):
            byte0 |= 0x02
        if doors.get("rl_open", False):
            byte0 |= 0x04
        if doors.get("rr_open", False):
            byte0 |= 0x08

        if doors.get("fl_locked", False):
            byte1 |= 0x01
        if doors.get("fr_locked", False):
            byte1 |= 0x02
        if doors.get("rl_locked", False):
            byte1 |= 0x04
        if doors.get("rr_locked", False):
            byte1 |= 0x08

        return bytes([byte0, byte1, 0, 0])

    def get_bus_load(self) -> float:
        """Get current bus load percentage"""
        return self.bus_load

    def get_statistics(self) -> dict:
        """Get interface statistics"""
        return {
            "tx_count": self.tx_count,
            "rx_count": self.rx_count,
            "bus_load": self.bus_load,
            "channel": self.channel,
            "bitrate": self.bitrate,
        }

    def get_message_log(self, can_id: Optional[int] = None) -> list[CANMessage]:
        """
        Get message log, optionally filtered by CAN ID
        Args:
            can_id: Optional CAN ID to filter by
        Returns:
            List of CAN messages
        """
        if can_id is None:
            return self.message_log.copy()
        return [m for m in self.message_log if m.id == can_id]

    def clear_log(self):
        """Clear message log"""
        self.message_log.clear()

    async def start(self):
        """Start CAN interface"""
        self.running = True
        logger.info(f"CAN interface started on {self.channel} at {self.bitrate} bps")

    async def stop(self):
        """Stop CAN interface"""
        self.running = False
        logger.info(f"CAN interface stopped")

    async def simulate_bus_traffic(self):
        """Simulate background CAN traffic"""
        while self.running:
            # Simulate periodic messages
            await asyncio.sleep(0.1)

            # Update bus load calculation
            if self.message_log:
                recent = [m for m in self.message_log if time.time() - m.timestamp < 1.0]
                bits = sum(m.dlc * 8 + 47 for m in recent)  # Including overhead
                self.bus_load = (bits / self.bitrate) * 100
            else:
                self.bus_load = 0.0


if __name__ == "__main__":
    # Quick test
    async def main():
        can = CANInterface()

        def on_bms_status(msg):
            data = can.parse_bms_status(msg.data)
            print(f"BMS Status: SOC={data.get('soc', 0):.1f}%")

        can.add_callback(can.BMS_STATUS_ID, on_bms_status)

        await can.start()

        # Send a test message
        data = can.build_bms_status(85.5, 400.0, 10.0, 25.0)
        await can.send(can.BMS_STATUS_ID, data)

        await asyncio.sleep(0.5)
        await can.stop()

    asyncio.run(main())
