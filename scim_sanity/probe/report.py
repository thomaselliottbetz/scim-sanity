"""Formats probe results as colored terminal output or structured JSON.

Two output modes are supported:

- **Terminal** — ANSI-colored output grouped by phase, with a summary line
  showing pass/fail/warn/skip/error counts, followed by a prioritised fix
  summary when failures are present.
- **JSON** — Machine-readable output with ``summary``, ``results``, and
  ``issues`` keys, suitable for CI/CD pipelines and downstream processing.
"""

import json
import sys
from typing import Any, Dict, List, Tuple


# ---------------------------------------------------------------------------
# Known issue patterns
# Each entry: (priority, title, message_substring_or_None, phase_prefix_or_None,
#              rationale, fix)
#
# message_substring: matched against ProbeResult.message (None = use phase_prefix)
# phase_prefix:      matched against ProbeResult.phase   (None = use message_substring)
# rationale:         one sentence explaining why this matters to a product/engineering audience
# fix:               one sentence describing the corrective action
# ---------------------------------------------------------------------------
_KNOWN_ISSUES: List[Tuple[str, str, Any, Any, str, str]] = [
    (
        "P1",
        "Wrong Content-Type on SCIM responses",
        "Content-Type should be application/scim+json",
        None,
        "Compliant clients inspect Content-Type before parsing — every response is "
        "rejected regardless of whether the body is otherwise correct.",
        "Set Content-Type: application/scim+json on all responses served from /scim/v2/",
    ),
    (
        "P2",
        "Discovery endpoints not implemented",
        None,
        "Phase 1",
        "Enterprise IdPs query these endpoints before provisioning to learn server "
        "capabilities; without them clients must hardcode assumptions or fail outright "
        "before sending a single user or group.",
        "Implement GET /ServiceProviderConfig, /Schemas, and /ResourceTypes",
    ),
    (
        "P3",
        "Missing meta timestamps on resource responses",
        "meta.created",
        None,
        "Without meta.lastModified, incremental sync is impossible — clients must "
        "full-scan every cycle or risk missing updates; meta.created is required for "
        "audit trails in regulated environments.",
        "Include meta.created and meta.lastModified in all resource representations",
    ),
    (
        "P4",
        "Missing Location header on 201 Created",
        "Location header should be present",
        None,
        "Clients that treat a missing Location as a failed create will silently discard "
        "every newly provisioned user or group with no error surfaced to the operator.",
        "Return Location: <base>/<resource>/<id> in all create (POST) responses",
    ),
    (
        "P5",
        "Missing status field in error response bodies",
        "missing required attribute 'status'",
        None,
        "Low impact in practice — the HTTP status code carries the same information — "
        "but programmatic error parsers that expect this field will fail or fall back "
        "to less specific handling.",
        'Include "status": "<http_code>" in all SCIM error response JSON bodies',
    ),
]


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
# Color is used only for error states (red); other statuses use bold or dim
# to remain legible on both dark and light terminal backgrounds.
_STATUS_SYMBOLS = {
    ProbeResult.PASS: ("PASS", "bold"),
    ProbeResult.FAIL: ("FAIL", "red"),
    ProbeResult.WARN: ("WARN", "dim"),
    ProbeResult.SKIP: ("SKIP", "dim"),
    ProbeResult.ERROR: ("ERR ", "red"),
}


def _terminal_wrap_issue_list(message: str, indent: str = "         ") -> str:
    """Insert terminal-friendly line breaks between semicolon-delimited issues."""
    return message.replace("; ", f";\n{indent}")


def _build_fix_summary(results: List[ProbeResult]) -> List[Dict[str, Any]]:
    """Derive a prioritised list of distinct issues from probe failures.

    Each entry contains priority label, title, fix hint, and count of
    affected tests.  Only issues with at least one affected test are returned.
    """
    failures = [r for r in results if r.status in (ProbeResult.FAIL, ProbeResult.ERROR)]
    issues = []
    matched_ids: set = set()
    for priority, title, msg_substr, phase_prefix, rationale, fix in _KNOWN_ISSUES:
        if msg_substr is not None:
            affected = [
                r for r in failures
                if msg_substr.lower() in r.message.lower()
            ]
        else:
            affected = [
                r for r in failures
                if r.phase and r.phase.startswith(phase_prefix)
            ]
        if affected:
            matched_ids.update(id(r) for r in affected)
            issues.append({
                "priority": priority,
                "title": title,
                "rationale": rationale,
                "fix": fix,
                "affected_tests": len(affected),
            })

    # Catch-all: surface failures that didn't match any known pattern
    unmatched = [r for r in failures if id(r) not in matched_ids]
    if unmatched:
        issues.append({
            "priority": "?",
            "title": f"{len(unmatched)} failure(s) not matched to a known root cause",
            "rationale": "These failures did not match any known issue pattern and require individual investigation.",
            "fix": "Review the individual test output above for specific error messages.",
            "affected_tests": len(unmatched),
        })

    return issues


def print_results(
    results: List[ProbeResult],
    json_output: bool = False,
    mode: str = "strict",
    version: str = "",
    timestamp: str = "",
):
    """Print the full probe report in terminal or JSON format."""
    if json_output:
        _print_json(results, mode=mode, version=version, timestamp=timestamp)
    else:
        _print_terminal(results, mode=mode, version=version, timestamp=timestamp)


def _print_terminal(
    results: List[ProbeResult],
    mode: str = "strict",
    version: str = "",
    timestamp: str = "",
):
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
    meta_parts = []
    if version:
        meta_parts.append(f"scim-sanity {version}")
    meta_parts.append(f"mode: {mode}")
    if timestamp:
        meta_parts.append(timestamp)
    print(_colorize("  " + "  |  ".join(meta_parts), "dim"))

    for result in results:
        # Print phase header when entering a new phase
        if result.phase and result.phase != current_phase:
            current_phase = result.phase
            print()
            print(_colorize(f"  {current_phase}", "bold"))
            print(_colorize("  " + "-" * 40, "dim"))

        symbol, color = _STATUS_SYMBOLS.get(result.status, ("??? ", "dim"))
        line = f"  [{_colorize(symbol, color)}] {result.name}"
        print(line)
        if result.message:
            print(f"         {_colorize(_terminal_wrap_issue_list(result.message), 'dim')}")

    # Summary footer
    print()
    print(_colorize("=" * 50, "dim"))
    summary_parts = []
    if passed:
        summary_parts.append(_colorize(f"{passed} passed", "bold"))
    if failed:
        summary_parts.append(_colorize(f"{failed} failed", "red"))
    if errored:
        summary_parts.append(_colorize(f"{errored} errors", "red"))
    if warned:
        summary_parts.append(_colorize(f"{warned} warnings", "dim"))
    if skipped:
        summary_parts.append(_colorize(f"{skipped} skipped", "dim"))
    summary_parts.append(f"{total} total")
    print("  " + ", ".join(summary_parts))

    # Fix summary — only shown when there are failures
    issues = _build_fix_summary(results)
    if issues:
        print()
        print(_colorize("  Fix Summary", "bold"))
        print(_colorize("  " + "-" * 40, "dim"))
        for issue in issues:
            n = issue["affected_tests"]
            tests_label = "test" if n == 1 else "tests"
            print(
                f"  [{_colorize(issue['priority'], 'red')}] "
                f"Trouble: {issue['title']} "
                f"{_colorize(f'({n} {tests_label} affected)', 'dim')}"
            )
            print(f"       Fix: {_colorize(issue['fix'], 'dim')}")
            print(f"       Rationale: {_colorize(issue['rationale'], 'dim')}")

    # Verdict
    print()
    print(_colorize("  " + "-" * 40, "dim"))
    if failed == 0 and errored == 0:
        print(_colorize("  Result: All tests passed.", "bold"))
    elif issues:
        known = [i for i in issues if i["priority"] != "?"]
        n_causes = len(known)
        causes_label = "root cause" if n_causes == 1 else "root causes"
        first = known[0]["priority"] if known else None
        resolve = f" Resolve {first} first." if first else ""
        print(_colorize(
            f"  Result: {n_causes} {causes_label} account for the failures.{resolve}",
            "dim",
        ))
    else:
        print(_colorize(
            f"  Result: {failed + errored} failure(s) — review individual test output for details.",
            "dim",
        ))

    print()


def _print_json(
    results: List[ProbeResult],
    mode: str = "strict",
    version: str = "",
    timestamp: str = "",
):
    """Render results as structured JSON with summary counts."""
    passed = sum(1 for r in results if r.status == ProbeResult.PASS)
    failed = sum(1 for r in results if r.status == ProbeResult.FAIL)
    warned = sum(1 for r in results if r.status == ProbeResult.WARN)
    skipped = sum(1 for r in results if r.status == ProbeResult.SKIP)
    errored = sum(1 for r in results if r.status == ProbeResult.ERROR)

    output = {
        "scim_sanity_version": version,
        "mode": mode,
        "timestamp": timestamp,
        "summary": {
            "total": len(results),
            "passed": passed,
            "failed": failed,
            "warnings": warned,
            "skipped": skipped,
            "errors": errored,
        },
        "issues": _build_fix_summary(results),
        "results": [r.to_dict() for r in results],
    }
    print(json.dumps(output, indent=2))
