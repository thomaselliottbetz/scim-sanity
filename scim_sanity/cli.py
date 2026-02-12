"""CLI interface for scim-sanity using Click (with graceful fallback).

Provides two modes of operation:

1. **Payload validation** (default): ``scim-sanity user.json`` validates a
   SCIM JSON payload against RFC 7643 rules.

2. **Server probe** (subcommand): ``scim-sanity probe <url>`` runs a CRUD
   lifecycle test sequence against a live SCIM server.

Click is an optional dependency.  If not installed, the CLI falls back to
manual ``sys.argv`` parsing via ``_main_no_click()``.

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

# Optional dependency: Click gives richer help output and subcommand routing,
# but the CLI works without it (same pattern as http_client.py with requests)
try:
    import click
    HAS_CLICK = True
except ImportError:
    HAS_CLICK = False

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
# No-Click fallback
# ---------------------------------------------------------------------------

def _main_no_click(args: list):
    """Fallback CLI when Click is not installed.  Parses sys.argv manually."""
    if not args or args[0] in ["-h", "--help"]:
        print("""scim-sanity: Validate SCIM 2.0 payloads & probe server conformance

Usage:
  scim-sanity <file>              Validate a SCIM resource file
  scim-sanity --patch <file>      Validate a SCIM PATCH operation file
  scim-sanity --stdin             Read JSON from stdin
  scim-sanity --stdin --patch     Validate PATCH from stdin
  scim-sanity probe <url>         Probe a SCIM server for conformance

Options:
  -h, --help     Show this help message
  --patch        Validate as PATCH operation
  --stdin        Read from stdin instead of file

Examples:
  scim-sanity user.json
  scim-sanity --patch patch.json
  echo '{"schemas":[...]}' | scim-sanity --stdin
  scim-sanity probe https://example.com/scim/v2 --token <token>
""")
        return 0

    # Route to probe subcommand if first arg is "probe"
    if args[0] == "probe":
        return _probe_no_click(args[1:])

    operation = "patch" if "--patch" in args else "full"
    read_stdin = "--stdin" in args

    if read_stdin:
        try:
            json_str = sys.stdin.read()
            data = json.loads(json_str)
            return _validate_and_report(data, operation)
        except json.JSONDecodeError as e:
            _print_error(f"Invalid JSON: {e}")
            return 1
        except Exception as e:
            _print_error(f"Error: {e}")
            return 1
    else:
        # Find file argument (first non-flag token)
        file_path = None
        for arg in args:
            if not arg.startswith("-"):
                file_path = arg
                break

        if not file_path:
            _print_error("No file specified")
            return 1

        try:
            with open(file_path, "r") as f:
                data = json.load(f)
            return _validate_and_report(data, operation, file_path)
        except FileNotFoundError:
            _print_error(f"File not found: {file_path}")
            return 1
        except json.JSONDecodeError as e:
            _print_error(f"Invalid JSON: {e}")
            return 1
        except Exception as e:
            _print_error(f"Error: {e}")
            return 1


def _probe_no_click(args: list) -> int:
    """Handle the ``probe`` subcommand without Click."""
    from .probe.runner import run_probe

    if not args or args[0] in ["-h", "--help"]:
        print("""scim-sanity probe: Test SCIM server conformance

Usage:
  scim-sanity probe <url> --token <token> --i-accept-side-effects
  scim-sanity probe <url> --username <user> --password <pass> --i-accept-side-effects

Options:
  --token                  Bearer token for authentication
  --username               Username for basic auth
  --password               Password for basic auth
  --tls-no-verify          Skip TLS certificate verification
  --skip-cleanup           Leave test resources on the server
  --json-output            Output results as JSON
  --resource               Test a specific resource type
  --strict / --compat      Strict (default) or compat validation mode
  --i-accept-side-effects  Required: acknowledge that probe creates/deletes resources
  --timeout                Per-request timeout in seconds (default: 30)
  --proxy                  HTTP/HTTPS proxy URL
  --ca-bundle              Path to custom CA certificate bundle
""")
        return 0

    url = args[0]
    token = _get_flag_value(args, "--token")
    username = _get_flag_value(args, "--username")
    password = _get_flag_value(args, "--password")
    tls_no_verify = "--tls-no-verify" in args
    skip_cleanup = "--skip-cleanup" in args
    json_output = "--json-output" in args
    resource = _get_flag_value(args, "--resource")
    strict = "--compat" not in args
    accept_side_effects = "--i-accept-side-effects" in args
    timeout_str = _get_flag_value(args, "--timeout")
    timeout = int(timeout_str) if timeout_str else 30
    proxy = _get_flag_value(args, "--proxy")
    ca_bundle = _get_flag_value(args, "--ca-bundle")

    return run_probe(
        url,
        token=token,
        username=username,
        password=password,
        tls_no_verify=tls_no_verify,
        skip_cleanup=skip_cleanup,
        json_output=json_output,
        resource_filter=resource,
        strict=strict,
        accept_side_effects=accept_side_effects,
        timeout=timeout,
    )


def _get_flag_value(args: list, flag: str) -> Optional[str]:
    """Extract the value following a ``--flag`` in an args list.  Returns None if not found."""
    try:
        idx = args.index(flag)
        if idx + 1 < len(args):
            return args[idx + 1]
    except ValueError:
        pass
    return None


# ---------------------------------------------------------------------------
# Click-based CLI (when Click is available)
# ---------------------------------------------------------------------------

if HAS_CLICK:
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
    @click.version_option(version="0.4.0")
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
        )
        sys.exit(exit_code)

else:
    def main():
        """Main entry point when Click is not available."""
        sys.exit(_main_no_click(sys.argv[1:]))


if __name__ == "__main__":
    main()
