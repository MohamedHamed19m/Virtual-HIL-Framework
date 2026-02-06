"""Door ECU Simulation Module"""

import asyncio
import logging
from dataclasses import dataclass, field
from enum import Enum
from typing import Dict, Optional, Callable

logger = logging.getLogger(__name__)


class DoorPosition(Enum):
    """Door position states"""

    CLOSED = "CLOSED"
    OPENING = "OPENING"
    OPEN = "OPEN"
    CLOSING = "CLOSING"
    BLOCKED = "BLOCKED"
    FAULT = "FAULT"


class LockState(Enum):
    """Door lock states"""

    LOCKED = "LOCKED"
    UNLOCKED = "UNLOCKED"
    CHILD_LOCKED = "CHILD_LOCKED"


@dataclass
class DoorState:
    """State of a single door"""

    position: DoorPosition = DoorPosition.CLOSED
    lock_state: LockState = LockState.LOCKED
    open_percentage: float = 0.0
    window_position: float = 0.0  # 0 = closed, 100 = fully open
    pinch_detected: bool = False


class DoorECU:
    """
    Simulates a Body Domain Controller (BDC) door ECU.

    Features:
    - Door position control (open/close)
    - Lock/unlock functionality
    - Window control
    - Pinch protection (anti-trap)
    - Child lock support
    - Fault injection and detection
    """

    def __init__(self, num_doors: int = 4):
        """
        Initialize Door ECU
        Args:
            num_doors: Number of doors to simulate (default: 4)
        """
        self.num_doors = num_doors
        self.doors: Dict[int, DoorState] = {}
        self.running = False
        self.position_callbacks: Dict[int, list[Callable]] = {}
        self.fault_state = False

        # Initialize all doors
        for i in range(num_doors):
            self.doors[i] = DoorState()
            self.position_callbacks[i] = []

    def add_position_callback(self, door_id: int, callback: Callable):
        """Add a callback to be notified of position changes"""
        if door_id in self.position_callbacks:
            self.position_callbacks[door_id].append(callback)

    def _notify_position_change(self, door_id: int):
        """Notify all callbacks of position change"""
        for callback in self.position_callbacks.get(door_id, []):
            try:
                callback(door_id, self.doors[door_id])
            except Exception as e:
                logger.error(f"Callback error: {e}")

    def get_door_position(self, door_id: int) -> DoorPosition:
        """Get current position state of a door"""
        if door_id not in self.doors:
            raise ValueError(f"Invalid door ID: {door_id}")
        return self.doors[door_id].position

    def get_door_open_percentage(self, door_id: int) -> float:
        """Get how open a door is (0-100%)"""
        if door_id not in self.doors:
            raise ValueError(f"Invalid door ID: {door_id}")
        return self.doors[door_id].open_percentage

    def is_locked(self, door_id: int) -> bool:
        """Check if door is locked"""
        if door_id not in self.doors:
            raise ValueError(f"Invalid door ID: {door_id}")
        return self.doors[door_id].lock_state != LockState.UNLOCKED

    def get_lock_state(self, door_id: int) -> LockState:
        """Get lock state of a door"""
        if door_id not in self.doors:
            raise ValueError(f"Invalid door ID: {door_id}")
        return self.doors[door_id].lock_state

    def get_window_position(self, door_id: int) -> float:
        """Get window position (0-100%)"""
        if door_id not in self.doors:
            raise ValueError(f"Invalid door ID: {door_id}")
        return self.doors[door_id].window_position

    async def open_door(self, door_id: int, target_percentage: float = 100.0):
        """
        Open a door to specified percentage
        Args:
            door_id: Door identifier
            target_percentage: How open to make the door (0-100)
        """
        if door_id not in self.doors:
            raise ValueError(f"Invalid door ID: {door_id}")

        door = self.doors[door_id]

        # Check if locked
        if door.lock_state == LockState.LOCKED:
            logger.warning(f"Door {door_id} is locked, cannot open")
            return

        # Check for fault state
        if self.fault_state:
            door.position = DoorPosition.FAULT
            return

        door.position = DoorPosition.OPENING

        # Simulate door movement
        steps = int(target_percentage - door.open_percentage)
        for _ in range(abs(steps)):
            if door.position != DoorPosition.OPENING:
                break
            if steps > 0:
                door.open_percentage = min(target_percentage, door.open_percentage + 5)
            else:
                door.open_percentage = max(target_percentage, door.open_percentage - 5)
            self._notify_position_change(door_id)
            await asyncio.sleep(0.05)

        door.position = DoorPosition.OPEN if door.open_percentage >= 100 else DoorPosition.CLOSED
        self._notify_position_change(door_id)

    async def close_door(self, door_id: int):
        """Close a door"""
        if door_id not in self.doors:
            raise ValueError(f"Invalid door ID: {door_id}")

        door = self.doors[door_id]
        door.position = DoorPosition.CLOSING

        # Simulate door movement
        while door.open_percentage > 0:
            if door.pinch_detected:
                door.position = DoorPosition.BLOCKED
                logger.warning(f"Pinch detected on door {door_id}, stopping")
                return

            door.open_percentage = max(0, door.open_percentage - 5)
            self._notify_position_change(door_id)
            await asyncio.sleep(0.05)

        door.position = DoorPosition.CLOSED
        self._notify_position_change(door_id)

    async def lock_door(self, door_id: int):
        """Lock a specific door"""
        if door_id not in self.doors:
            raise ValueError(f"Invalid door ID: {door_id}")
        self.doors[door_id].lock_state = LockState.LOCKED

    async def unlock_door(self, door_id: int):
        """Unlock a specific door"""
        if door_id not in self.doors:
            raise ValueError(f"Invalid door ID: {door_id}")
        self.doors[door_id].lock_state = LockState.UNLOCKED

    async def lock_all_doors(self):
        """Lock all doors"""
        for door_id in self.doors:
            await self.lock_door(door_id)

    async def unlock_all_doors(self):
        """Unlock all doors"""
        for door_id in self.doors:
            await self.unlock_door(door_id)

    def set_child_lock(self, door_id: int, enabled: bool):
        """Enable or disable child lock on rear doors"""
        if door_id not in self.doors:
            raise ValueError(f"Invalid door ID: {door_id}")
        self.doors[door_id].lock_state = LockState.CHILD_LOCKED if enabled else LockState.LOCKED

    async def open_window(self, door_id: int, percentage: float = 100.0):
        """Open window on specified door"""
        if door_id not in self.doors:
            raise ValueError(f"Invalid door ID: {door_id}")

        door = self.doors[door_id]
        target = max(0, min(100, percentage))

        while door.window_position < target:
            door.window_position = min(target, door.window_position + 10)
            await asyncio.sleep(0.1)

    async def close_window(self, door_id: int):
        """Close window on specified door"""
        if door_id not in self.doors:
            raise ValueError(f"Invalid door ID: {door_id}")

        door = self.doors[door_id]
        while door.window_position > 0:
            door.window_position = max(0, door.window_position - 10)
            await asyncio.sleep(0.1)

    def trigger_pinch(self, door_id: int):
        """Trigger pinch detection (for testing)"""
        if door_id in self.doors:
            self.doors[door_id].pinch_detected = True

    def clear_pinch(self, door_id: int):
        """Clear pinch detection"""
        if door_id in self.doors:
            self.doors[door_id].pinch_detected = False

    def set_fault_state(self, fault: bool):
        """Set fault state for testing"""
        self.fault_state = fault

    def get_faults(self) -> list:
        """Get list of active faults"""
        faults = []

        for door_id, door in self.doors.items():
            if door.position == DoorPosition.FAULT:
                faults.append(f"DOOR_{door_id}_FAULT")
            if door.position == DoorPosition.BLOCKED:
                faults.append(f"DOOR_{door_id}_BLOCKED")

        return faults

    def get_dtc(self) -> Optional[str]:
        """Get Diagnostic Trouble Code"""
        faults = self.get_faults()
        if faults:
            return f"BDC_{faults[0]}"
        return None

    async def start(self):
        """Start the ECU simulation"""
        self.running = True
        logger.info("Door ECU simulation started")

    async def stop(self):
        """Stop the ECU simulation"""
        self.running = False
        logger.info("Door ECU simulation stopped")

    def to_dict(self) -> dict:
        """Export current state as dictionary"""
        return {
            door_id: {
                "position": door.position.value,
                "lock_state": door.lock_state.value,
                "open_percentage": door.open_percentage,
                "window_position": door.window_position,
            }
            for door_id, door in self.doors.items()
        }


if __name__ == "__main__":
    # Quick test of the Door ECU
    async def main():
        ecu = DoorECU(num_doors=4)
        await ecu.start()

        print(f"Door 0 position: {ecu.get_door_position(0)}")
        print(f"Door 0 locked: {ecu.is_locked(0)}")

        # Unlock and open door
        await ecu.unlock_door(0)
        await ecu.open_door(0, 100)
        print(f"After open - Door 0: {ecu.get_door_open_percentage(0)}%")

        # Close door
        await ecu.close_door(0)
        print(f"After close - Door 0: {ecu.get_door_open_percentage(0)}%")

        await ecu.stop()

    asyncio.run(main())
