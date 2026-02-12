"""Formats probe results as colored terminal output or structured JSON.

Two output modes are supported:

- **Terminal** — ANSI-colored output grouped by phase, with a summary line
  showing pass/fail/warn/skip/error counts.
- **JSON** — Machine-readable output with ``summary`` and ``results`` keys,
  suitable for CI/CD pipelines and downstream processing.
"""

import json
import sys
from typing import Any, Dict, List


class ProbeResult:
    """A single conformance test result.

    Attributes:
        name:    Human-readable test name (e.g. ``POST /Users``).
        status:  One of PASS, FAIL, WARN, SKIP, ERROR.
        message: Optional detail about the outcome.
        details: Optional extended detail (not shown in terminal, included in JSON).
        phase:   Test phase label for grouping in output (e.g. ``Phase 2 — User CRUD Lifecycle``).

    Note: This class was originally named ``TestResult`` but was renamed to
    ``ProbeResult`` to avoid pytest's ``Test*`` collection pattern.
    """

    PASS = "pass"
    FAIL = "fail"
    WARN = "warn"
    SKIP = "skip"
    ERROR = "error"

    def __init__(
        self,
        name: str,
        status: str,
        message: str = "",
        details: str = "",
        phase: str = "",
    ):
        self.name = name
        self.status = status
        self.message = message
        self.details = details
        self.phase = phase

    def to_dict(self) -> Dict[str, Any]:
        """Serialize to dict for JSON output.  Omits empty fields."""
        d: Dict[str, Any] = {
            "name": self.name,
            "status": self.status,
        }
        if self.message:
            d["message"] = self.message
        if self.details:
            d["details"] = self.details
        if self.phase:
            d["phase"] = self.phase
        return d


def _colorize(text: str, color: str) -> str:
    """Apply ANSI color codes.  Returns plain text when stdout is not a TTY."""
    colors = {
        "red": "\033[91m",
        "green": "\033[92m",
        "yellow": "\033[93m",
        "blue": "\033[94m",
        "cyan": "\033[96m",
        "bold": "\033[1m",
        "dim": "\033[2m",
        "reset": "\033[0m",
    }
    if not sys.stdout.isatty():
        return text
    return f"{colors.get(color, '')}{text}{colors['reset']}"


# Maps ProbeResult status to (display label, ANSI color)
_STATUS_SYMBOLS = {
    ProbeResult.PASS: ("PASS", "green"),
    ProbeResult.FAIL: ("FAIL", "red"),
    ProbeResult.WARN: ("WARN", "yellow"),
    ProbeResult.SKIP: ("SKIP", "yellow"),
    ProbeResult.ERROR: ("ERR ", "red"),
}


def print_results(results: List[ProbeResult], json_output: bool = False):
    """Print the full probe report in terminal or JSON format."""
    if json_output:
        _print_json(results)
    else:
        _print_terminal(results)


def _print_terminal(results: List[ProbeResult]):
    """Render results as ANSI-colored terminal output, grouped by phase."""
    current_phase = ""
    passed = sum(1 for r in results if r.status == ProbeResult.PASS)
    failed = sum(1 for r in results if r.status == ProbeResult.FAIL)
    warned = sum(1 for r in results if r.status == ProbeResult.WARN)
    skipped = sum(1 for r in results if r.status == ProbeResult.SKIP)
    errored = sum(1 for r in results if r.status == ProbeResult.ERROR)
    total = len(results)

    print()
    print(_colorize("SCIM Server Conformance Probe", "bold"))
    print(_colorize("=" * 50, "dim"))

    for result in results:
        # Print phase header when entering a new phase
        if result.phase and result.phase != current_phase:
            current_phase = result.phase
            print()
            print(_colorize(f"  {current_phase}", "cyan"))
            print(_colorize("  " + "-" * 40, "dim"))

        symbol, color = _STATUS_SYMBOLS.get(result.status, ("??? ", "dim"))
        line = f"  [{_colorize(symbol, color)}] {result.name}"
        print(line)
        if result.message:
            print(f"         {_colorize(result.message, 'dim')}")

    # Summary footer
    print()
    print(_colorize("=" * 50, "dim"))
    summary_parts = []
    if passed:
        summary_parts.append(_colorize(f"{passed} passed", "green"))
    if failed:
        summary_parts.append(_colorize(f"{failed} failed", "red"))
    if errored:
        summary_parts.append(_colorize(f"{errored} errors", "red"))
    if warned:
        summary_parts.append(_colorize(f"{warned} warnings", "yellow"))
    if skipped:
        summary_parts.append(_colorize(f"{skipped} skipped", "yellow"))
    summary_parts.append(f"{total} total")
    print("  " + ", ".join(summary_parts))
    print()


def _print_json(results: List[ProbeResult]):
    """Render results as structured JSON with summary counts."""
    passed = sum(1 for r in results if r.status == ProbeResult.PASS)
    failed = sum(1 for r in results if r.status == ProbeResult.FAIL)
    warned = sum(1 for r in results if r.status == ProbeResult.WARN)
    skipped = sum(1 for r in results if r.status == ProbeResult.SKIP)
    errored = sum(1 for r in results if r.status == ProbeResult.ERROR)

    output = {
        "summary": {
            "total": len(results),
            "passed": passed,
            "failed": failed,
            "warnings": warned,
            "skipped": skipped,
            "errors": errored,
        },
        "results": [r.to_dict() for r in results],
    }
    print(json.dumps(output, indent=2))
