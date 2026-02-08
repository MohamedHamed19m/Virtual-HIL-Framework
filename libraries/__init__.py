"""Virtual HIL Framework - Robot Framework Libraries"""

__version__ = "0.1.0"

from .ECUSimulatorLibrary import ECUSimulatorLibrary
from .ECUSimulatorHTTPLibrary import ECUSimulatorHTTPLibrary  # ADD THIS LINE
from .CANLibrary import CANLibrary
from .DiagnosticLibrary import DiagnosticLibrary
from .FaultInjectionLibrary import FaultInjectionLibrary

__all__ = [
    "ECUSimulatorLibrary",
    "ECUSimulatorHTTPLibrary",  # ADD THIS LINE
    "CANLibrary",
    "DiagnosticLibrary",
    "FaultInjectionLibrary",
]