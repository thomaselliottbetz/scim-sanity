"""CLI interface for scim-sanity.

Provides two modes of operation:

1. **Payload validation** (default): ``scim-sanity user.json`` validates a
   SCIM JSON payload against RFC 7643 rules.

2. **Server probe** (subcommand): ``scim-sanity probe <url>`` runs a CRUD
   lifecycle test sequence against a live SCIM server.

Architecture note: The CLI uses a custom ``_SCIMGroup(click.Group)`` class
to allow ``scim-sanity user.json`` (positional file argument) alongside
``scim-sanity probe <url>`` (subcommand).  Standard Click groups don't
support positional args on the group itself because they collide with
subcommand name routing.  ``_SCIMGroup.parse_args()`` detects whether the
first positional token is a known subcommand; if not, it rewrites it as
``--file <arg>`` before delegating to Click's normal parsing.
"""

import sys
import json
from typing import Optional

import click

from .validator import validate_file, validate_string, SCIMValidator


# ---------------------------------------------------------------------------
# Shared helpers (used by both Click and no-Click paths)
# ---------------------------------------------------------------------------

def _colorize(text: str, color: str) -> str:
    """Apply ANSI color codes.  Returns plain text when stdout is not a TTY."""
    colors = {
        "red": "\033[91m",
        "green": "\033[92m",
        "yellow": "\033[93m",
        "blue": "\033[94m",
        "reset": "\033[0m",
        "bold": "\033[1m",
    }
    if not sys.stdout.isatty():
        return text
    return f"{colors.get(color, '')}{text}{colors['reset']}"


def _print_error(message: str, path: str = "", line: Optional[int] = None):
    """Print a validation error with location context."""
    loc = f" at {path}" if path else ""
    line_info = f" (line {line})" if line else ""
    error_msg = f"❌ {message}{loc}{line_info}"
    print(_colorize(error_msg, "red"))


def _print_success(message: str):
    """Print a success message."""
    print(_colorize(f"✅ {message}", "green"))


def _validate_and_report(data: dict, operation: str = "full", file_path: Optional[str] = None) -> int:
    """Validate SCIM data and print human-readable results.  Returns exit code."""
    validator = SCIMValidator()
    is_valid, errors = validator.validate(data, operation)

    if is_valid:
        resource_type = "PATCH operation" if operation == "patch" else "SCIM resource"
        _print_success(f"Valid {resource_type}")
        return 0
    else:
        print(_colorize(f"\nFound {len(errors)} error(s):\n", "bold"))
        for error in errors:
            _print_error(error.message, error.path, error.line)
        return 1


# ---------------------------------------------------------------------------
# Click-based CLI
# ---------------------------------------------------------------------------

class _SCIMGroup(click.Group):
    """Custom Click group that supports positional file args alongside subcommands.

    Click groups normally don't accept positional arguments because they
    collide with subcommand names.  This class intercepts ``parse_args``
    to detect whether the first positional token is a known subcommand.
    If it isn't, the token is rewritten as ``--file <arg>`` so it routes
    to the default validate behavior instead of failing with
    "Path 'user.json' does not exist" as a subcommand lookup.
    """

    def parse_args(self, ctx, args):
        if args and not args[0].startswith("-") and args[0] not in self.commands:
            args = ["--file", args[0]] + args[1:]
        return super().parse_args(ctx, args)


@click.group(cls=_SCIMGroup, invoke_without_command=True)
@click.option("--file", "file", default=None, type=click.Path(exists=True),
              help="SCIM JSON file to validate", hidden=True)
@click.option("--patch", is_flag=True, help="Validate as PATCH operation")
@click.option("--stdin", "read_stdin", is_flag=True, help="Read JSON from stdin")
@click.version_option(version="0.5.1")
@click.pass_context
def main(ctx, file: Optional[str], patch: bool, read_stdin: bool):
    """Validate SCIM 2.0 payloads & probe server conformance (RFC 7643/7644).

    Catch SCIM integration bugs before they hit production.

    \b
    Usage:
      scim-sanity <file>              Validate a SCIM resource file
      scim-sanity --patch <file>      Validate a SCIM PATCH operation file
      scim-sanity --stdin             Read JSON from stdin
      scim-sanity probe <url>         Probe a SCIM server for conformance
    """
    # If a subcommand (e.g. "probe") was invoked, skip default validation
    if ctx.invoked_subcommand is not None:
        return

    operation = "patch" if patch else "full"

    if read_stdin:
        try:
            json_str = sys.stdin.read()
            data = json.loads(json_str)
            exit_code = _validate_and_report(data, operation)
            sys.exit(exit_code)
        except json.JSONDecodeError as e:
            _print_error(f"Invalid JSON: {e}")
            sys.exit(1)
        except Exception as e:
            _print_error(f"Error: {e}")
            sys.exit(1)
    elif file:
        try:
            with open(file, "r") as f:
                data = json.load(f)
            exit_code = _validate_and_report(data, operation, file)
            sys.exit(exit_code)
        except FileNotFoundError:
            _print_error(f"File not found: {file}")
            sys.exit(1)
        except json.JSONDecodeError as e:
            _print_error(f"Invalid JSON: {e}")
            sys.exit(1)
        except Exception as e:
            _print_error(f"Error: {e}")
            sys.exit(1)
    else:
        click.echo(ctx.get_help())
        sys.exit(1)


@main.command()
@click.argument("url")
@click.option("--token", default=None, help="Bearer token for authentication")
@click.option("--username", default=None, help="Username for basic auth")
@click.option("--password", default=None, help="Password for basic auth")
@click.option("--tls-no-verify", is_flag=True, help="Skip TLS certificate verification")
@click.option("--skip-cleanup", is_flag=True, help="Leave test resources on the server")
@click.option("--json-output", is_flag=True, help="Output results as JSON")
@click.option("--resource", default=None, help="Test a specific resource type (User, Group, Agent, AgenticApplication)")
@click.option("--strict/--compat", default=True, help="Strict (default) or compat validation mode")
@click.option("--i-accept-side-effects", is_flag=True, help="Acknowledge that probe creates/deletes resources on target server")
@click.option("--timeout", default=30, type=int, help="Per-request timeout in seconds")
@click.option("--proxy", default=None, help="HTTP/HTTPS proxy URL")
@click.option("--ca-bundle", default=None, type=click.Path(exists=True), help="Path to custom CA certificate bundle")
def probe(url, token, username, password, tls_no_verify, skip_cleanup,
          json_output, resource, strict, i_accept_side_effects, timeout,
          proxy, ca_bundle):
    """Probe a live SCIM server for RFC 7643/7644 conformance.

    Runs a CRUD lifecycle test sequence against the server at URL,
    including discovery, User/Group/Agent/AgenticApplication operations,
    search, and error handling.

    WARNING: This command creates, modifies, and deletes real resources
    on the target server.  You must pass --i-accept-side-effects to proceed.

    \b
    Examples:
      scim-sanity probe https://example.com/scim/v2 --token <token> --i-accept-side-effects
      scim-sanity probe <url> --token <token> --tls-no-verify --i-accept-side-effects
      scim-sanity probe <url> --token <token> --compat --i-accept-side-effects
      scim-sanity probe <url> --token <token> --resource Agent --i-accept-side-effects
    """
    from .probe.runner import run_probe

    exit_code = run_probe(
        url,
        token=token,
        username=username,
        password=password,
        tls_no_verify=tls_no_verify,
        skip_cleanup=skip_cleanup,
        json_output=json_output,
        resource_filter=resource,
        strict=strict,
        accept_side_effects=i_accept_side_effects,
        timeout=timeout,
        proxy=proxy,
        ca_bundle=ca_bundle,
    )
    sys.exit(exit_code)


if __name__ == "__main__":
    main()
