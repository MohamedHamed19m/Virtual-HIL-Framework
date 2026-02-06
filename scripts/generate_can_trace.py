#!/usr/bin/env python3
"""
Virtual HIL Framework - CAN Trace Generator

This script generates CAN trace files for testing and simulation.
"""

import argparse
import json
import struct
import sys
from dataclasses import dataclass
from datetime import datetime
from pathlib import Path
from typing import List, Optional


@dataclass
class CANMessage:
    """Represents a CAN message for tracing"""

    timestamp: float
    channel: int
    id: int
    dlc: int
    data: bytes
    direction: str = "TX"  # TX or RX
    comment: str = ""


class CANTraceGenerator:
    """Generate CAN trace files in various formats"""

    # Standard CAN IDs
    BMS_STATUS_ID = 0x100
    BMS_CELL_DATA_ID = 0x101
    BMS_FAULT_ID = 0x102
    BDC_STATUS_ID = 0x200
    BDC_DOOR_POS_ID = 0x201
    BDC_LOCK_STATUS_ID = 0x202

    def __init__(self):
        self.messages: List[CANMessage] = []
        self.current_time = 0.0

    def add_message(self, msg: CANMessage):
        """Add a message to the trace"""
        self.messages.append(msg)
        self.current_time = max(self.current_time, msg.timestamp)

    def generate_bms_status(
        self,
        soc: float = 85.5,
        voltage: float = 400.0,
        current: float = 10.0,
        temperature: float = 25.0,
    ) -> CANMessage:
        """Generate a BMS status message"""
        data = struct.pack(
            "<BBhhhBB",
            int(soc * 2),  # SOC
            100,  # SOH
            int(voltage * 10),  # Voltage
            int(current * 10),  # Current
            int(temperature + 40),  # Temperature
            0,  # Reserved
            0x00,  # Status
        )

        return CANMessage(
            timestamp=self.current_time + 0.1,
            channel=0,
            id=self.BMS_STATUS_ID,
            dlc=8,
            data=data,
            direction="TX",
            comment="BMS Status",
        )

    def generate_door_status(
        self,
        fl_open: bool = False,
        fr_open: bool = False,
        rl_open: bool = False,
        rr_open: bool = False,
        fl_locked: bool = True,
        fr_locked: bool = True,
        rl_locked: bool = True,
        rr_locked: bool = True,
    ) -> CANMessage:
        """Generate a door status message"""
        byte0 = 0
        byte1 = 0

        if fl_open:
            byte0 |= 0x01
        if fr_open:
            byte0 |= 0x02
        if rl_open:
            byte0 |= 0x04
        if rr_open:
            byte0 |= 0x08

        if fl_locked:
            byte1 |= 0x01
        if fr_locked:
            byte1 |= 0x02
        if rl_locked:
            byte1 |= 0x04
        if rr_locked:
            byte1 |= 0x08

        data = bytes([byte0, byte1, 0, 0, 0, 0, 0, 0])

        return CANMessage(
            timestamp=self.current_time + 0.1,
            channel=0,
            id=self.BDC_STATUS_ID,
            dlc=8,
            data=data,
            direction="TX",
            comment="Door Status",
        )

    def generate_sequence(self, duration: float = 10.0, frequency: float = 10.0):
        """Generate a sequence of periodic messages"""
        period = 1.0 / frequency
        end_time = self.current_time + duration

        while self.current_time < end_time:
            # Add BMS status
            bms = self.generate_bms_status()
            self.add_message(bms)

            # Add door status
            door = self.generate_door_status()
            self.add_message(door)

            self.current_time += period

    def save_csv(self, filename: Path):
        """Save trace as CSV file"""
        with open(filename, "w") as f:
            f.write("timestamp,channel,id,dlc,data,direction,comment\n")
            for msg in self.messages:
                data_hex = msg.data.hex().upper()
                f.write(
                    f"{msg.timestamp:.6f},{msg.channel},{msg.id:03X},{msg.dlc},"
                    f"{data_hex},{msg.direction},{msg.comment}\n"
                )
        print(f"Saved CSV trace to {filename}")

    def save_json(self, filename: Path):
        """Save trace as JSON file"""
        trace_data = {
            "version": "1.0",
            "generated_at": datetime.now().isoformat(),
            "message_count": len(self.messages),
            "messages": [
                {
                    "timestamp": msg.timestamp,
                    "channel": msg.channel,
                    "id": msg.id,
                    "dlc": msg.dlc,
                    "data": msg.data.hex(),
                    "direction": msg.direction,
                    "comment": msg.comment,
                }
                for msg in self.messages
            ],
        }

        with open(filename, "w") as f:
            json.dump(trace_data, f, indent=2)
        print(f"Saved JSON trace to {filename}")

    def save_candump(self, filename: Path):
        """Save trace in candump format"""
        with open(filename, "w") as f:
            for msg in self.messages:
                timestamp_str = f"({msg.timestamp:.6f})"
                data_hex = " ".join(f"{b:02X}" for b in msg.data)
                f.write(f"{timestamp_str} can{msg.channel}  #{msg.id:03X}#{data_hex}\n")
        print(f"Saved candump trace to {filename}")

    def save_blf(self, filename: Path):
        """Save trace as BLF (Binary Log Format) - simplified"""
        # BLF is a complex binary format; this is a placeholder
        print(f"BLF format not fully implemented, saving as JSON instead")
        self.save_json(filename.with_suffix(".json"))


def main():
    parser = argparse.ArgumentParser(
        description="Generate CAN trace files for Virtual HIL Framework"
    )
    parser.add_argument(
        "--output", "-o", type=Path, default="can_trace.csv", help="Output file path"
    )
    parser.add_argument(
        "--format",
        "-f",
        choices=["csv", "json", "candump", "blf"],
        default="csv",
        help="Output format",
    )
    parser.add_argument(
        "--duration", "-d", type=float, default=10.0, help="Trace duration in seconds"
    )
    parser.add_argument(
        "--frequency", "-F", type=float, default=10.0, help="Message frequency (Hz)"
    )
    parser.add_argument("--soc", type=float, default=85.5, help="Battery SOC for BMS messages")
    parser.add_argument(
        "--voltage", type=float, default=400.0, help="Battery voltage for BMS messages"
    )

    args = parser.parse_args()

    # Create generator
    gen = CANTraceGenerator()

    print(f"Generating CAN trace...")
    print(f"  Duration: {args.duration}s")
    print(f"  Frequency: {args.frequency}Hz")
    print(f"  Format: {args.format}")

    # Generate messages
    gen.generate_sequence(duration=args.duration, frequency=args.frequency)

    print(f"  Generated {len(gen.messages)} messages")

    # Save trace
    output_file = args.output
    if args.format != "csv" and output_file.suffix == ".csv":
        output_file = output_file.with_suffix(f".{args.format}")

    if args.format == "csv":
        gen.save_csv(output_file)
    elif args.format == "json":
        gen.save_json(output_file)
    elif args.format == "candump":
        gen.save_candump(output_file)
    elif args.format == "blf":
        gen.save_blf(output_file)

    print("Done!")


if __name__ == "__main__":
    main()
