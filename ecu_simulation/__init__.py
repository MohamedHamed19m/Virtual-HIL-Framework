"""Virtual HIL Framework - ECU Simulation Module"""

__version__ = "0.1.0"

from .battery_ecu import BatteryECU
from .door_ecu import DoorECU
from .can_interface import CANInterface
from .diagnostic_server import DiagnosticServer
from .rest_interface import RESTInterface

__all__ = [
    "BatteryECU",
    "DoorECU",
    "CANInterface",
    "DiagnosticServer",
    "RESTInterface",
]
