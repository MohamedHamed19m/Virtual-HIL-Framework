#!/usr/bin/env python3
"""
Virtual HIL Framework - Log Analyzer

This script analyzes test logs and generates reports.
"""

import argparse
import json
import re
from dataclasses import dataclass, field
from datetime import datetime
from pathlib import Path
from typing import List, Dict, Optional


@dataclass
class TestResult:
    """Represents a test result"""

    name: str
    status: str  # PASS, FAIL, SKIP
    duration: float
    message: str = ""
    tags: List[str] = field(default_factory=list)
    suite: str = ""


@dataclass
class LogStatistics:
    """Statistics from log analysis"""

    total_tests: int = 0
    passed: int = 0
    failed: int = 0
    skipped: int = 0
    total_duration: float = 0.0
    failures: List[TestResult] = field(default_factory=list)


class LogAnalyzer:
    """Analyze Robot Framework and application logs"""

    def __init__(self):
        self.stats = LogStatistics()

    def analyze_robot_log(self, log_file: Path) -> LogStatistics:
        """Analyze Robot Framework output.xml or log.html"""
        print(f"Analyzing Robot Framework log: {log_file}")

        if not log_file.exists():
            print(f"Log file not found: {log_file}")
            return self.stats

        # Try to parse output.xml if it exists
        output_xml = log_file.parent / "output.xml"
        if output_xml.exists():
            return self._parse_output_xml(output_xml)

        # Otherwise, parse log.html
        return self._parse_log_html(log_file)

    def _parse_output_xml(self, xml_file: Path) -> LogStatistics:
        """Parse Robot Framework output.xml"""
        try:
            import xml.etree.ElementTree as ET

            tree = ET.parse(xml_file)
            root = tree.getroot()

            stats = LogStatistics()

            for test in root.iter("test"):
                name = test.get("name", "")
                status = test.get("status", "UNKNOWN")

                # Get duration
                elapsed = test.find(".//elapsed")
                duration = float(elapsed.text) if elapsed is not None else 0.0

                # Get message if failed
                message_elem = test.find(".//msg[@level='FAIL']")
                message = message_elem.text if message_elem is not None else ""

                result = TestResult(name=name, status=status, duration=duration, message=message)

                stats.total_tests += 1
                stats.total_duration += duration

                if status == "PASS":
                    stats.passed += 1
                elif status == "FAIL":
                    stats.failed += 1
                    stats.failures.append(result)
                elif status == "SKIP":
                    stats.skipped += 1

            self.stats = stats
            return stats

        except Exception as e:
            print(f"Error parsing XML: {e}")
            return self.stats

    def _parse_log_html(self, log_file: Path) -> LogStatistics:
        """Parse Robot Framework log.html (basic regex parsing)"""
        content = log_file.read_text()

        stats = LogStatistics()

        # Extract test results using regex
        test_pattern = r'class="test-(pass|fail|skip)".*?<td>(.*?)</td>'
        matches = re.findall(test_pattern, content, re.DOTALL)

        for status, name in matches:
            result = TestResult(name=name.strip(), status=status.upper(), duration=0.0)

            stats.total_tests += 1

            if status == "pass":
                stats.passed += 1
            elif status == "fail":
                stats.failed += 1
                stats.failures.append(result)
            elif status == "skip":
                stats.skipped += 1

        self.stats = stats
        return stats

    def analyze_app_log(self, log_file: Path) -> Dict:
        """Analyze application log file"""
        print(f"Analyzing application log: {log_file}")

        if not log_file.exists():
            return {}

        content = log_file.read_text()

        analysis = {
            "total_lines": len(content.splitlines()),
            "errors": [],
            "warnings": [],
            "exceptions": [],
        }

        # Find errors
        error_pattern = r"\[(?:ERROR|CRITICAL)\].*?(?:\n|$)"
        for match in re.finditer(error_pattern, content):
            analysis["errors"].append(match.group().strip())

        # Find warnings
        warning_pattern = r"\[WARNING\].*?(?:\n|$)"
        for match in re.finditer(warning_pattern, content):
            analysis["warnings"].append(match.group().strip())

        # Find exceptions
        exception_pattern = r"Traceback.*?(?=\n\n|\Z)"
        for match in re.finditer(exception_pattern, content, re.DOTALL):
            analysis["exceptions"].append(match.group().strip())

        return analysis

    def generate_report(self, output_file: Path):
        """Generate analysis report"""
        report = {
            "generated_at": datetime.now().isoformat(),
            "test_statistics": {
                "total_tests": self.stats.total_tests,
                "passed": self.stats.passed,
                "failed": self.stats.failed,
                "skipped": self.stats.skipped,
                "pass_rate": self.stats.passed / self.stats.total_tests
                if self.stats.total_tests > 0
                else 0,
                "total_duration": self.stats.total_duration,
            },
            "failures": [
                {"name": f.name, "message": f.message, "duration": f.duration}
                for f in self.stats.failures
            ],
        }

        if output_file.suffix == ".json":
            with open(output_file, "w") as f:
                json.dump(report, f, indent=2)
        else:
            # Generate markdown report
            self._generate_markdown_report(report, output_file)

        print(f"Report saved to {output_file}")

    def _generate_markdown_report(self, report: Dict, output_file: Path):
        """Generate markdown report"""
        lines = [
            "# Test Analysis Report",
            f"Generated: {report['generated_at']}",
            "",
            "## Test Statistics",
            "",
            f"- **Total Tests**: {report['test_statistics']['total_tests']}",
            f"- **Passed**: {report['test_statistics']['passed']}",
            f"- **Failed**: {report['test_statistics']['failed']}",
            f"- **Skipped**: {report['test_statistics']['skipped']}",
            f"- **Pass Rate**: {report['test_statistics']['pass_rate']:.1%}",
            f"- **Duration**: {report['test_statistics']['total_duration']:.2f}s",
            "",
        ]

        if report["failures"]:
            lines.extend(["## Failures", ""])
            for failure in report["failures"]:
                lines.extend(
                    [
                        f"### {failure['name']}",
                        f"- **Duration**: {failure['duration']:.2f}s",
                        f"- **Message**: {failure['message']}",
                        "",
                    ]
                )

        output_file.write_text("\n".join(lines))


def main():
    parser = argparse.ArgumentParser(description="Analyze Virtual HIL Framework test logs")
    parser.add_argument(
        "log_file", type=Path, help="Log file to analyze (output.xml, log.html, or app log)"
    )
    parser.add_argument(
        "--output", "-o", type=Path, default="test_report.json", help="Output report file"
    )
    parser.add_argument(
        "--format", "-f", choices=["json", "markdown"], default="json", help="Report format"
    )

    args = parser.parse_args()

    analyzer = LogAnalyzer()

    # Determine log type and analyze
    log_name = args.log_file.name.lower()
    if "output.xml" in log_name or "log.html" in log_name:
        analyzer.analyze_robot_log(args.log_file)
    else:
        app_analysis = analyzer.analyze_app_log(args.log_file)
        print(f"\nApplication Log Analysis:")
        print(f"  Total lines: {app_analysis.get('total_lines', 0)}")
        print(f"  Errors: {len(app_analysis.get('errors', []))}")
        print(f"  Warnings: {len(app_analysis.get('warnings', []))}")
        print(f"  Exceptions: {len(app_analysis.get('exceptions', []))}")

    # Generate report
    if analyzer.stats.total_tests > 0:
        output_file = args.output
        if args.format == "markdown" and output_file.suffix == ".json":
            output_file = output_file.with_suffix(".md")

        analyzer.generate_report(output_file)

        # Print summary
        print(f"\nTest Summary:")
        print(f"  Total: {analyzer.stats.total_tests}")
        print(f"  Passed: {analyzer.stats.passed}")
        print(f"  Failed: {analyzer.stats.failed}")
        print(f"  Pass Rate: {analyzer.stats.passed / analyzer.stats.total_tests * 100:.1f}%")


if __name__ == "__main__":
    main()
