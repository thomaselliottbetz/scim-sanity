"""CLI interface for scim-sanity using Click (with graceful fallback)."""

import sys
import json
from typing import Optional

try:
    import click
    HAS_CLICK = True
except ImportError:
    HAS_CLICK = False

from .validator import validate_file, validate_string, SCIMValidator


def _colorize(text: str, color: str) -> str:
    """Colorize text using ANSI codes (works even without click)."""
    colors = {
        "red": "\033[91m",
        "green": "\033[92m",
        "yellow": "\033[93m",
        "blue": "\033[94m",
        "reset": "\033[0m",
        "bold": "\033[1m",
    }
    if not sys.stdout.isatty():
        return text  # No colors if not a TTY
    return f"{colors.get(color, '')}{text}{colors['reset']}"


def _print_error(message: str, path: str = "", line: Optional[int] = None):
    """Print a validation error with color."""
    loc = f" at {path}" if path else ""
    line_info = f" (line {line})" if line else ""
    error_msg = f"❌ {message}{loc}{line_info}"
    print(_colorize(error_msg, "red"))


def _print_success(message: str):
    """Print a success message with color."""
    print(_colorize(f"✅ {message}", "green"))


def _validate_and_report(data: dict, operation: str = "full", file_path: Optional[str] = None) -> int:
    """Validate data and print results. Returns exit code."""
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


def _main_no_click(args: list):
    """Fallback main function when Click is not available."""
    if not args or args[0] in ["-h", "--help"]:
        print("""scim-sanity: Validate SCIM 2.0 User, Group, Agent, and AgenticApplication payloads

Usage:
  scim-sanity <file>              Validate a SCIM resource file
  scim-sanity --patch <file>      Validate a SCIM PATCH operation file
  scim-sanity --stdin             Read JSON from stdin
  scim-sanity --stdin --patch     Validate PATCH from stdin

Options:
  -h, --help     Show this help message
  --patch        Validate as PATCH operation
  --stdin        Read from stdin instead of file

Examples:
  scim-sanity user.json
  scim-sanity --patch patch.json
  echo '{"schemas":[...]}' | scim-sanity --stdin
""")
        return 0
    
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
        # Find file argument (first non-flag)
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


if HAS_CLICK:
    @click.command()
    @click.argument("file", required=False, type=click.Path(exists=True))
    @click.option("--patch", is_flag=True, help="Validate as PATCH operation")
    @click.option("--stdin", is_flag=True, help="Read JSON from stdin")
    @click.version_option(version="0.2.0")
    def main(file: Optional[str], patch: bool, stdin: bool):
        """Validate SCIM 2.0 User, Group, Agent, and AgenticApplication payloads (RFC 7643/7644).
        
        Catch SCIM integration bugs before they hit production.
        
        Examples:
        
        \b
          scim-sanity user.json
          scim-sanity --patch patch.json
          echo '{"schemas":[...]}' | scim-sanity --stdin
        """
        operation = "patch" if patch else "full"
        
        if stdin:
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
            click.echo(click.get_current_context().get_help())
            sys.exit(1)
else:
    def main():
        """Main entry point when Click is not available."""
        sys.exit(_main_no_click(sys.argv[1:]))


if __name__ == "__main__":
    main()

