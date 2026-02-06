#!/usr/bin/env python3
"""
Virtual HIL Framework - Statistics Extractor

This script extracts statistics from test results and logs.
"""

import argparse
import json
import re
from dataclasses import dataclass, asdict
from pathlib import Path
from typing import Dict, List, Any


@dataclass
class TestStats:
    """Test execution statistics"""

    total: int = 0
    passed: int = 0
    failed: int = 0
    skipped: int = 0
    pass_rate: float = 0.0
    avg_duration: float = 0.0
    total_duration: float = 0.0


@dataclass
class ECUMetrics:
    """ECU performance metrics"""

    name: str
    cpu_usage: float = 0.0
    memory_usage: float = 0.0
    response_time_ms: float = 0.0
    message_rate: float = 0.0


@dataclass
class CANMetrics:
    """CAN bus metrics"""

    total_messages: int = 0
    bus_load_percent: float = 0.0
    error_count: int = 0
    tx_count: int = 0
    rx_count: int = 0


class StatsExtractor:
    """Extract statistics from various sources"""

    def extract_from_robot_output(self, output_xml: Path) -> Dict[str, Any]:
        """Extract stats from Robot Framework output.xml"""
        try:
            import xml.etree.ElementTree as ET

            tree = ET.parse(output_xml)
            root = tree.getroot()

            stats = TestStats()

            for test in root.iter("test"):
                stats.total += 1
                status = test.get("status")

                if status == "PASS":
                    stats.passed += 1
                elif status == "FAIL":
                    stats.failed += 1
                elif status == "SKIP":
                    stats.skipped += 1

                elapsed = test.find(".//elapsed")
                if elapsed is not None:
                    stats.total_duration += float(elapsed.text)

            if stats.total > 0:
                stats.pass_rate = (stats.passed / stats.total) * 100
                stats.avg_duration = stats.total_duration / stats.total

            return asdict(stats)

        except Exception as e:
            return {"error": str(e)}

    def extract_from_log_file(self, log_file: Path) -> Dict[str, Any]:
        """Extract metrics from application log file"""
        content = log_file.read_text()

        metrics = {
            "total_lines": len(content.splitlines()),
            "error_count": len(re.findall(r"\[ERROR\]", content)),
            "warning_count": len(re.findall(r"\[WARNING\]", content)),
            "exception_count": len(re.findall(r"Traceback", content)),
        }

        # Extract timing information
        time_pattern = r"executed in ([\d.]+)s"
        times = re.findall(time_pattern, content)
        if times:
            metrics["avg_execution_time"] = sum(float(t) for t in times) / len(times)

        return metrics

    def extract_can_metrics(self, log_file: Path) -> Dict[str, Any]:
        """Extract CAN bus metrics from log"""
        content = log_file.read_text()

        metrics = CANMetrics()

        # Count CAN messages
        metrics.total_messages = len(re.findall(r"CAN (?:TX|RX):", content))

        # Count TX vs RX
        metrics.tx_count = len(re.findall(r"CAN TX:", content))
        metrics.rx_count = len(re.findall(r"CAN RX:", content))

        # Find bus load
        load_pattern = r"bus load: ([\d.]+)"
        loads = re.findall(load_pattern, content)
        if loads:
            metrics.bus_load_percent = float(loads[-1])

        # Count errors
        metrics.error_count = len(re.findall(r"CAN error", content))

        return asdict(metrics)

    def generate_comparison(self, baseline_file: Path, current_file: Path) -> Dict[str, Any]:
        """Compare current stats with baseline"""
        baseline = json.loads(baseline_file.read_text())
        current = json.loads(current_file.read_text())

        comparison = {
            "test_count_delta": current.get("total", 0) - baseline.get("total", 0),
            "pass_rate_delta": current.get("pass_rate", 0) - baseline.get("pass_rate", 0),
            "duration_delta": current.get("total_duration", 0) - baseline.get("total_duration", 0),
        }

        return comparison

    def export_trends(self, stats_files: List[Path], output_file: Path):
        """Export trend data from multiple stat files"""
        trends = []

        for stats_file in sorted(stats_files):
            stats = json.loads(stats_file.read_text())
            stats["source"] = stats_file.name
            trends.append(stats)

        output_file.write_text(json.dumps(trends, indent=2))
        print(f"Exported trends for {len(trends)} data points to {output_file}")


def main():
    parser = argparse.ArgumentParser(description="Extract statistics from test results")
    parser.add_argument("input_file", type=Path, help="Input file (output.xml, log, or JSON stats)")
    parser.add_argument("--output", "-o", type=Path, default="stats.json", help="Output JSON file")
    parser.add_argument(
        "--type", "-t", choices=["robot", "log", "can"], default="robot", help="Input file type"
    )
    parser.add_argument("--compare", "-c", type=Path, help="Baseline file for comparison")
    parser.add_argument(
        "--trend", action="store_true", help="Generate trend data from multiple files"
    )
    parser.add_argument(
        "--trend-dir", type=Path, help="Directory containing stat files for trend analysis"
    )

    args = parser.parse_args()

    extractor = StatsExtractor()

    if args.trend and args.trend_dir:
        # Generate trend data
        stats_files = list(args.trend_dir.glob("*.json"))
        extractor.export_trends(stats_files, args.output)
        return

    # Extract stats based on type
    if args.type == "robot":
        stats = extractor.extract_from_robot_output(args.input_file)
    elif args.type == "log":
        stats = extractor.extract_from_log_file(args.input_file)
    elif args.type == "can":
        stats = extractor.extract_can_metrics(args.input_file)
    else:
        stats = {"error": "Unknown type"}

    # Add comparison if requested
    if args.compare and args.compare.exists():
        stats["comparison"] = extractor.generate_comparison(args.compare, args.output)

    # Write output
    args.output.write_text(json.dumps(stats, indent=2))
    print(f"Statistics extracted to {args.output}")

    # Print summary
    if "total" in stats:
        print(f"\nSummary:")
        print(f"  Total: {stats['total']}")
        print(f"  Passed: {stats['passed']}")
        print(f"  Pass Rate: {stats['pass_rate']:.1f}%")
    if "total_messages" in stats:
        print(f"\nCAN Metrics:")
        print(f"  Messages: {stats['total_messages']}")
        print(f"  Bus Load: {stats['bus_load_percent']:.1f}%")


if __name__ == "__main__":
    main()
