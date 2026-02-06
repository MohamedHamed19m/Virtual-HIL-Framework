"""REST API Interface for ECU Simulation"""

import asyncio
import logging
from dataclasses import dataclass, asdict
from typing import Dict, Any, Optional
from datetime import datetime
import json

logger = logging.getLogger(__name__)


@dataclass
class APIResponse:
    """Standard API response wrapper"""

    success: bool
    data: Any = None
    error: Optional[str] = None
    timestamp: str = ""

    def __post_init__(self):
        if not self.timestamp:
            self.timestamp = datetime.utcnow().isoformat()

    def to_json(self) -> str:
        """Convert to JSON string"""
        return json.dumps(asdict(self))


class RESTInterface:
    """
    REST API interface for ECU simulation control.

    This class provides a REST-like interface for controlling
    ECUs programmatically. In a real implementation, this would
    use FastAPI, Flask, or similar web framework.

    Features:
    - ECU state queries
    - ECU control commands
    - Fault injection
    - Signal monitoring
    """

    def __init__(self, battery_ecu=None, door_ecu=None, can_interface=None):
        """
        Initialize REST interface
        Args:
            battery_ecu: BatteryECU instance
            door_ecu: DoorECU instance
            can_interface: CANInterface instance
        """
        self.battery_ecu = battery_ecu
        self.door_ecu = door_ecu
        self.can_interface = can_interface
        self.running = False
        self.signal_subscribers: Dict[str, list] = {}

    async def get_battery_status(self) -> APIResponse:
        """Get battery ECU status"""
        if not self.battery_ecu:
            return APIResponse(False, error="Battery ECU not available")

        try:
            data = self.battery_ecu.to_dict()
            return APIResponse(True, data=data)
        except Exception as e:
            return APIResponse(False, error=str(e))

    async def get_door_status(self, door_id: Optional[int] = None) -> APIResponse:
        """
        Get door status
        Args:
            door_id: Optional door ID, if None returns all doors
        """
        if not self.door_ecu:
            return APIResponse(False, error="Door ECU not available")

        try:
            if door_id is not None:
                if door_id not in self.door_ecu.doors:
                    return APIResponse(False, error=f"Invalid door ID: {door_id}")

                door = self.door_ecu.doors[door_id]
                data = {
                    "door_id": door_id,
                    "position": door.position.value,
                    "lock_state": door.lock_state.value,
                    "open_percentage": door.open_percentage,
                    "window_position": door.window_position,
                }
            else:
                data = self.door_ecu.to_dict()

            return APIResponse(True, data=data)
        except Exception as e:
            return APIResponse(False, error=str(e))

    async def control_door(self, door_id: int, command: str, **kwargs) -> APIResponse:
        """
        Control a door
        Args:
            door_id: Door identifier
            command: Command (open, close, lock, unlock, open_window, close_window)
            **kwargs: Additional parameters (e.g., target_percentage)
        """
        if not self.door_ecu:
            return APIResponse(False, error="Door ECU not available")

        try:
            if door_id not in self.door_ecu.doors:
                return APIResponse(False, error=f"Invalid door ID: {door_id}")

            match command:
                case "open":
                    target = kwargs.get("target_percentage", 100.0)
                    await self.door_ecu.open_door(door_id, target)
                case "close":
                    await self.door_ecu.close_door(door_id)
                case "lock":
                    await self.door_ecu.lock_door(door_id)
                case "unlock":
                    await self.door_ecu.unlock_door(door_id)
                case "open_window":
                    target = kwargs.get("target_percentage", 100.0)
                    await self.door_ecu.open_window(door_id, target)
                case "close_window":
                    await self.door_ecu.close_window(door_id)
                case _:
                    return APIResponse(False, error=f"Unknown command: {command}")

            return APIResponse(True, data={"door_id": door_id, "command": command})

        except Exception as e:
            return APIResponse(False, error=str(e))

    async def control_all_doors(self, command: str) -> APIResponse:
        """
        Control all doors
        Args:
            command: Command (lock_all, unlock_all)
        """
        if not self.door_ecu:
            return APIResponse(False, error="Door ECU not available")

        try:
            match command:
                case "lock_all":
                    await self.door_ecu.lock_all_doors()
                case "unlock_all":
                    await self.door_ecu.unlock_all_doors()
                case _:
                    return APIResponse(False, error=f"Unknown command: {command}")

            return APIResponse(True, data={"command": command})

        except Exception as e:
            return APIResponse(False, error=str(e))

    async def inject_fault(self, ecu: str, fault_type: str, **kwargs) -> APIResponse:
        """
        Inject a fault for testing
        Args:
            ecu: ECU type (battery, door)
            fault_type: Type of fault to inject
            **kwargs: Fault-specific parameters
        """
        try:
            if ecu == "battery" and self.battery_ecu:
                match fault_type:
                    case "overvoltage":
                        cell_id = kwargs.get("cell_id", 0)
                        self.battery_ecu.set_cell_voltage(cell_id, 4.3)
                    case "undervoltage":
                        cell_id = kwargs.get("cell_id", 0)
                        self.battery_ecu.set_cell_voltage(cell_id, 2.5)
                    case "overtemperature":
                        cell_id = kwargs.get("cell_id", 0)
                        self.battery_ecu.set_cell_temperature(cell_id, 70.0)
                    case _:
                        return APIResponse(False, error=f"Unknown fault type: {fault_type}")

                return APIResponse(True, data={"ecu": ecu, "fault": fault_type})

            elif ecu == "door" and self.door_ecu:
                match fault_type:
                    case "block":
                        door_id = kwargs.get("door_id", 0)
                        self.door_ecu.trigger_pinch(door_id)
                    case "fault":
                        door_id = kwargs.get("door_id", 0)
                        self.door_ecu.set_fault_state(True)
                    case "clear_fault":
                        self.door_ecu.set_fault_state(False)
                    case _:
                        return APIResponse(False, error=f"Unknown fault type: {fault_type}")

                return APIResponse(True, data={"ecu": ecu, "fault": fault_type})

            return APIResponse(False, error=f"Unknown ECU: {ecu}")

        except Exception as e:
            return APIResponse(False, error=str(e))

    async def clear_faults(self, ecu: str) -> APIResponse:
        """
        Clear all faults for an ECU
        Args:
            ecu: ECU type (battery, door)
        """
        try:
            if ecu == "battery" and self.battery_ecu:
                self.battery_ecu.clear_dtc()
            elif ecu == "door" and self.door_ecu:
                self.door_ecu.set_fault_state(False)
                for door_id in self.door_ecu.doors:
                    self.door_ecu.clear_pinch(door_id)
            else:
                return APIResponse(False, error=f"Unknown ECU: {ecu}")

            return APIResponse(True, data={"ecu": ecu})

        except Exception as e:
            return APIResponse(False, error=str(e))

    async def get_can_statistics(self) -> APIResponse:
        """Get CAN interface statistics"""
        if not self.can_interface:
            return APIResponse(False, error="CAN interface not available")

        try:
            data = self.can_interface.get_statistics()
            return APIResponse(True, data=data)

        except Exception as e:
            return APIResponse(False, error=str(e))

    async def send_can_message(self, can_id: int, data: str) -> APIResponse:
        """
        Send a CAN message
        Args:
            can_id: CAN message ID
            data: Hex-encoded data bytes
        """
        if not self.can_interface:
            return APIResponse(False, error="CAN interface not available")

        try:
            data_bytes = bytes.fromhex(data)
            success = await self.can_interface.send(can_id, data_bytes)

            if success:
                return APIResponse(True, data={"can_id": can_id, "data": data})
            else:
                return APIResponse(False, error="Failed to send message")

        except ValueError:
            return APIResponse(False, error="Invalid hex data")

        except Exception as e:
            return APIResponse(False, error=str(e))

    async def simulate_charge(self, current: float, duration: float) -> APIResponse:
        """
        Simulate battery charging/discharging
        Args:
            current: Current in Amps (positive = charging)
            duration: Duration in seconds
        """
        if not self.battery_ecu:
            return APIResponse(False, error="Battery ECU not available")

        try:
            self.battery_ecu.simulate_charge(current, duration)
            return APIResponse(
                True,
                data={
                    "current": current,
                    "duration": duration,
                    "new_soc": self.battery_ecu.get_soc(),
                },
            )

        except Exception as e:
            return APIResponse(False, error=str(e))

    async def get_dtc(self, ecu: str) -> APIResponse:
        """
        Get DTC from an ECU
        Args:
            ecu: ECU type (battery, door)
        """
        try:
            if ecu == "battery" and self.battery_ecu:
                dtc = self.battery_ecu.get_dtc()
                faults = self.battery_ecu.check_faults()
                return APIResponse(True, data={"dtc": dtc, "faults": faults})

            elif ecu == "door" and self.door_ecu:
                dtc = self.door_ecu.get_dtc()
                faults = self.door_ecu.get_faults()
                return APIResponse(True, data={"dtc": dtc, "faults": faults})

            return APIResponse(False, error=f"Unknown ECU: {ecu}")

        except Exception as e:
            return APIResponse(False, error=str(e))

    async def health_check(self) -> APIResponse:
        """Health check endpoint"""
        status = {
            "battery_ecu": self.battery_ecu is not None,
            "door_ecu": self.door_ecu is not None,
            "can_interface": self.can_interface is not None,
            "running": self.running,
        }
        return APIResponse(True, data=status)

    async def start(self):
        """Start REST interface"""
        self.running = True
        logger.info("REST interface started")

    async def stop(self):
        """Stop REST interface"""
        self.running = False
        logger.info("REST interface stopped")


# Example FastAPI implementation (not used in simulation mode)
"""
from fastapi import FastAPI, HTTPException
from pydantic import BaseModel

app = FastAPI(title="Virtual HIL Framework API")
rest_interface = None

class DoorControlRequest(BaseModel):
    door_id: int
    command: str
    target_percentage: Optional[float] = None

@app.on_event("startup")
async def startup():
    global rest_interface
    # Initialize with your ECU instances
    rest_interface = RESTInterface()
    await rest_interface.start()

@app.get("/api/battery/status")
async def get_battery_status():
    response = await rest_interface.get_battery_status()
    if not response.success:
        raise HTTPException(400, response.error)
    return response

@app.post("/api/door/control")
async def control_door(request: DoorControlRequest):
    response = await rest_interface.control_door(
        request.door_id, request.command,
        target_percentage=request.target_percentage
    )
    if not response.success:
        raise HTTPException(400, response.error)
    return response
"""


if __name__ == "__main__":
    # Quick test
    async def main():
        from .battery_ecu import BatteryECU
        from .door_ecu import DoorECU

        battery = BatteryECU()
        door = DoorECU()

        rest = RESTInterface(battery_ecu=battery, door_ecu=door)
        await rest.start()

        # Test endpoints
        print("Health check:", await rest.health_check())
        print("Battery status:", await rest.get_battery_status())
        print("Door status:", await rest.get_door_status(0))

        await rest.stop()

    asyncio.run(main())
