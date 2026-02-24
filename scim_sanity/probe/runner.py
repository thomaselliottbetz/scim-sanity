"""Orchestrates the full SCIM conformance test sequence.

This is the main entry point for the probe.  ``run_probe()`` connects to a
live SCIM server, runs 7 phases of conformance tests, cleans up created
resources, and returns an exit code (0 = all pass, 1 = failures).

Safety mechanisms:
- Requires ``accept_side_effects=True`` before executing (CLI flag: ``--i-accept-side-effects``)
- All test resources use the ``TEST_PREFIX`` for namespace isolation
- Rapid lifecycle tests are capped at ``MAX_RAPID_AGENTS``
- Created resources are tracked and cleaned up in reverse order
"""

import sys
from typing import Any, Dict, List, Optional, Set

import datetime

from ..http_client import SCIMClient
from ..response_validator import ServerResponseValidator
from .. import __version__
from .report import ProbeResult, print_results
from .tests import (
    test_discovery,
    discover_supported_resources,
    test_user_lifecycle,
    test_group_lifecycle,
    test_agent_lifecycle,
    test_agentic_application_lifecycle,
    test_agent_rapid_lifecycle,
    test_search,
    test_error_handling,
)

# Namespace prefix — all test resources use this in their names/userNames
# to avoid collisions with real data on the target server
TEST_PREFIX = "scim-sanity-test-"

# Hard cap on agents created during rapid lifecycle tests to prevent
# runaway resource creation on production servers
MAX_RAPID_AGENTS = 10


def run_probe(
    base_url: str,
    token: Optional[str] = None,
    username: Optional[str] = None,
    password: Optional[str] = None,
    tls_no_verify: bool = False,
    skip_cleanup: bool = False,
    json_output: bool = False,
    resource_filter: Optional[str] = None,
    strict: bool = True,
    accept_side_effects: bool = False,
    timeout: int = 30,
    rapid_agent_count: int = MAX_RAPID_AGENTS,
    proxy: Optional[str] = None,
    ca_bundle: Optional[str] = None,
) -> int:
    """Run the full conformance probe and return an exit code.

    Returns:
        0 if all tests pass (warnings are OK), 1 if any test fails or errors.

    Args:
        base_url:             Root URL of the SCIM endpoint.
        token:                Bearer token for authentication.
        username:             Username for HTTP Basic authentication.
        password:             Password for HTTP Basic authentication.
        tls_no_verify:        Skip TLS certificate verification.
        skip_cleanup:         If True, leave test resources on the server.
        json_output:          If True, output results as JSON instead of terminal.
        resource_filter:      Test only a specific resource type (e.g. ``"Agent"``).
        strict:               If True, spec-pedantic mode.  If False, compat mode.
        accept_side_effects:  Must be True to proceed — the probe creates, modifies,
                              and deletes real resources on the target server.
        timeout:              Per-request timeout in seconds.
        rapid_agent_count:    Number of agents for rapid lifecycle test (capped).
        proxy:                HTTP/HTTPS proxy URL (e.g. ``"http://proxy.example.com:8080"``).
        ca_bundle:            Path to a CA bundle file for TLS certificate verification.
    """
    # --- Safety gate: require explicit consent before running ----------------
    if not accept_side_effects:
        _print_side_effect_warning(base_url, resource_filter, json_output)
        return 1

    rapid_agent_count = min(rapid_agent_count, MAX_RAPID_AGENTS)

    client = SCIMClient(
        base_url,
        token=token,
        username=username,
        password=password,
        tls_no_verify=tls_no_verify,
        timeout=timeout,
        proxy=proxy,
        ca_bundle=ca_bundle,
    )

    rv = ServerResponseValidator(strict=strict)

    results: List[ProbeResult] = []
    created_resources: List[Dict[str, Any]] = []  # tracks resources for cleanup

    mode_label = "strict" if strict else "compat"
    run_timestamp = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")

    # Phase 1: Discovery
    results.extend(test_discovery(client, rv))

    # Discover which resource types the server supports
    supported = discover_supported_resources(client)

    # If user requested a specific resource type, narrow scope
    requested = {resource_filter} if resource_filter else supported

    # Phase 2: User CRUD
    if "User" in requested:
        results.extend(test_user_lifecycle(client, rv, created_resources))
    else:
        results.append(ProbeResult(
            "User CRUD Lifecycle", ProbeResult.SKIP,
            message="User not in scope", phase="Phase 2 — User CRUD Lifecycle",
        ))

    # Phase 3: Group CRUD
    if "Group" in requested:
        results.extend(test_group_lifecycle(client, rv, created_resources))
    else:
        results.append(ProbeResult(
            "Group CRUD Lifecycle", ProbeResult.SKIP,
            message="Group not in scope", phase="Phase 3 — Group CRUD Lifecycle",
        ))

    # Phase 4: Agent CRUD (only if server advertises support)
    if "Agent" in requested and "Agent" in supported:
        results.extend(test_agent_lifecycle(client, rv, created_resources))
    else:
        reason = "not supported by server" if "Agent" not in supported else "not in scope"
        results.append(ProbeResult(
            "Agent CRUD Lifecycle", ProbeResult.SKIP,
            message=f"Agent {reason}", phase="Phase 4 — Agent CRUD Lifecycle",
        ))

    # Phase 5: AgenticApplication CRUD (only if server advertises support)
    if "AgenticApplication" in requested and "AgenticApplication" in supported:
        results.extend(test_agentic_application_lifecycle(client, rv, created_resources))
    else:
        reason = "not supported by server" if "AgenticApplication" not in supported else "not in scope"
        results.append(ProbeResult(
            "AgenticApplication CRUD Lifecycle", ProbeResult.SKIP,
            message=f"AgenticApplication {reason}",
            phase="Phase 5 — AgenticApplication CRUD Lifecycle",
        ))

    # Phase 5a: Agent Rapid Lifecycle (only if server supports Agents)
    if "Agent" in requested and "Agent" in supported:
        results.extend(test_agent_rapid_lifecycle(
            client, created_resources, count=rapid_agent_count,
        ))
    else:
        results.append(ProbeResult(
            "Agent Rapid Lifecycle", ProbeResult.SKIP,
            message="Agent not supported or not in scope",
            phase="Phase 5a — Agent Rapid Lifecycle",
        ))

    # Phase 6: Search
    results.extend(test_search(client, rv))

    # Phase 7: Error Handling
    results.extend(test_error_handling(client, rv))

    # Cleanup: delete test resources in reverse order (groups before users)
    if not skip_cleanup and created_resources:
        _cleanup(client, created_resources, results)

    # Output results
    print_results(results, json_output=json_output, mode=mode_label,
                  version=__version__, timestamp=run_timestamp)

    # Exit code: warnings are OK, only FAIL and ERROR cause exit code 1
    has_failures = any(
        r.status in (ProbeResult.FAIL, ProbeResult.ERROR)
        for r in results
    )
    return 1 if has_failures else 0


def _print_side_effect_warning(base_url: str, resource_filter: Optional[str], json_output: bool):
    """Warn the user that the probe will create/modify/delete resources and exit."""
    resources = resource_filter or "User, Group, Agent, AgenticApplication"
    if json_output:
        import json
        print(json.dumps({
            "error": "Side-effect consent required",
            "message": (
                f"The probe will create, modify, and delete test resources "
                f"({resources}) on {base_url}. "
                f"All test resources use the prefix '{TEST_PREFIX}'. "
                f"Pass --i-accept-side-effects to proceed."
            ),
        }, indent=2))
    else:
        print(
            f"\n  The probe will create, modify, and delete test resources\n"
            f"  ({resources}) on:\n\n"
            f"    {base_url}\n\n"
            f"  All test resources use the prefix '{TEST_PREFIX}'.\n"
            f"  Pass --i-accept-side-effects to proceed.\n"
        )


def _cleanup(
    client: SCIMClient,
    created_resources: List[Dict[str, Any]],
    results: List[ProbeResult],
):
    """Delete all created test resources in reverse order.

    Reverse order ensures dependent resources (e.g., group members) are
    removed before parent resources.  Cleanup results are appended to
    the results list.
    """
    phase = "Cleanup"
    for resource in reversed(created_resources):
        endpoint = resource["endpoint"]
        rid = resource["id"]
        try:
            resp = client.delete(f"{endpoint}/{rid}")
            if resp.status_code == 204:
                results.append(ProbeResult(
                    f"DELETE {endpoint}/{rid}", ProbeResult.PASS, phase=phase,
                ))
            else:
                results.append(ProbeResult(
                    f"DELETE {endpoint}/{rid}", ProbeResult.FAIL,
                    message=f"Expected 204, got {resp.status_code}", phase=phase,
                ))
        except Exception as exc:
            results.append(ProbeResult(
                f"DELETE {endpoint}/{rid}", ProbeResult.ERROR,
                message=str(exc), phase=phase,
            ))
