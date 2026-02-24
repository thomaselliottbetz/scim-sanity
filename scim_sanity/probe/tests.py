"""Individual conformance test functions for the SCIM probe.

Each public ``test_*`` function takes a ``SCIMClient`` (and usually a
``ServerResponseValidator``) and returns a list of ``ProbeResult`` objects.
Tests are grouped by phase:

- Phase 1: Discovery (/ServiceProviderConfig, /Schemas, /ResourceTypes)
- Phase 2-5: CRUD lifecycles (User, Group, Agent, AgenticApplication)
- Phase 5a: Agent rapid lifecycle (ephemeral create/delete)
- Phase 6: Search (ListResponse, filtering, pagination)
- Phase 7: Error handling (404, 400 responses)

The ``_crud_lifecycle`` helper implements the generic POST-GET-PUT-PATCH-DELETE
sequence shared by all resource types.
"""

import time
import urllib.parse
from typing import Any, Callable, Dict, List, Optional, Set

from ..http_client import SCIMClient, SCIMResponse
from ..response_validator import ServerResponseValidator, ServerValidationError, WARN
from ..payload_factory import (
    make_user,
    make_group,
    make_agent,
    make_agentic_application,
    make_patch,
    update_user_display_name,
)
from .report import ProbeResult


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def _errors_str(errors: List[ServerValidationError]) -> str:
    """Join validation errors into a semicolon-separated string for display."""
    return "; ".join(str(e) for e in errors)


def _validation_results(
    test_name: str,
    phase: str,
    ok: bool,
    errors: List[ServerValidationError],
    pass_message: str = "",
) -> List[ProbeResult]:
    """Convert a ``(ok, errors)`` validation result into ``ProbeResult`` entries.

    Separates FAIL-severity errors from WARN-severity errors so that
    compat-mode warnings appear as WARN results rather than FAILs.
    A single test may produce both a PASS/FAIL result and one or more
    WARN results in the same call.

    Args:
        pass_message: Optional note shown on PASS results to clarify what was verified.
    """
    results: List[ProbeResult] = []
    fails = [e for e in errors if e.severity != WARN]
    warns = [e for e in errors if e.severity == WARN]

    if ok and not fails:
        results.append(ProbeResult(test_name, ProbeResult.PASS, message=pass_message, phase=phase))
    else:
        results.append(ProbeResult(
            test_name, ProbeResult.FAIL,
            message=_errors_str(fails) if fails else _errors_str(errors),
            phase=phase,
        ))

    # Emit a separate WARN result for each warning-severity error
    for w in warns:
        results.append(ProbeResult(
            test_name, ProbeResult.WARN,
            message=str(w), phase=phase,
        ))

    return results


def _retry_post_on_500(
    client: SCIMClient,
    endpoint: str,
    payload: Dict[str, Any],
    delay: float = 2.0,
) -> Optional[SCIMResponse]:
    """Retry a POST that returned 500 after a brief delay using the same headers.

    Returns the successful response if the retry returns 2xx, or None if it
    also fails. Used to distinguish transient 500s from structural failures
    before escalating to content-type diagnosis.
    """
    time.sleep(delay)
    try:
        resp = client.post(endpoint, payload)
        if resp.status_code in (200, 201):
            return resp
    except Exception:
        pass
    return None


def _diagnose_content_type_rejection(
    client: SCIMClient,
    endpoint: str,
    payload: Dict[str, Any],
    created_resources: List[Dict[str, Any]],
) -> Optional[str]:
    """When a POST returns 500, retry with Content-Type: application/json to
    determine whether the server is rejecting application/scim+json requests.

    Returns a specific RFC-cited error string if the retry succeeds, or None
    if the retry also fails (indicating a different root cause).
    Cleans up any resource created during the diagnostic retry.
    """
    try:
        resp = client.post(endpoint, payload,
                           extra_headers={"Content-Type": "application/json"})
        if resp.status_code in (200, 201):
            body = resp.json() if resp.body else None
            if body and "id" in body:
                resource_id = body["id"]
                try:
                    del_resp = client.delete(f"{endpoint}/{resource_id}")
                    if del_resp.status_code != 204:
                        created_resources.append({"endpoint": endpoint, "id": resource_id})
                except Exception:
                    created_resources.append({"endpoint": endpoint, "id": resource_id})
            return (
                "Server rejected Content-Type: application/scim+json with 500 "
                "but accepted application/json — server MUST accept "
                "application/scim+json per RFC 7644 §8.2"
            )
    except Exception:
        pass
    return None


def _crud_lifecycle(
    client: SCIMClient,
    rv: ServerResponseValidator,
    resource_type: str,
    endpoint: str,
    make_fn: Callable[[], Dict[str, Any]],
    phase: str,
    created_resources: List[Dict[str, Any]],
    display_name_field: str = "displayName",
) -> List[ProbeResult]:
    """Run a full CRUD lifecycle for a resource type.

    Sequence: POST (201) -> GET (200) -> PUT (200 + verify) -> PATCH (200 +
    verify) -> DELETE (204) -> GET (404).  For Groups, also tests PATCH
    add/remove members on multi-valued attributes.

    Created resources are tracked in ``created_resources`` for cleanup.
    If DELETE succeeds during the test, the resource is removed from the
    cleanup list to avoid double-delete.

    Args:
        client:             HTTP client for the target SCIM server.
        rv:                 Response validator (strict or compat mode).
        resource_type:      SCIM resource type name (e.g. ``User``).
        endpoint:           URL path (e.g. ``/Users``).
        make_fn:            Factory function that generates a test payload.
        phase:              Display label for this phase.
        created_resources:  Mutable list tracking resources for cleanup.
        display_name_field: Attribute name to modify during PUT test.
    """
    results: List[ProbeResult] = []

    # -- CREATE (POST) -------------------------------------------------------
    payload = make_fn()
    try:
        resp = client.post(endpoint, payload)
    except Exception as exc:
        results.append(ProbeResult(
            f"POST {endpoint}", ProbeResult.ERROR,
            message=str(exc), phase=phase,
        ))
        return results

    # Diagnostic: if 500, first check for transience, then content-type rejection
    if resp.status_code == 500:
        retry_resp = _retry_post_on_500(client, endpoint, payload)
        if retry_resp is not None:
            # Transient 500 — warn and continue lifecycle with the retry response
            results.append(ProbeResult(
                f"POST {endpoint}", ProbeResult.WARN,
                message=(
                    "Server returned 500 on first attempt but succeeded on retry — "
                    "server has transient instability (RFC 7644 §3.3 requires reliable 201)"
                ),
                phase=phase,
            ))
            resp = retry_resp
        else:
            # Consistent 500 — check whether server rejects application/scim+json
            hint = _diagnose_content_type_rejection(client, endpoint, payload, created_resources)
            if hint:
                results.append(ProbeResult(
                    f"POST {endpoint}", ProbeResult.FAIL,
                    message=hint, phase=phase,
                ))
                results.append(ProbeResult(
                    f"GET {endpoint}/{{id}}", ProbeResult.SKIP,
                    message="Skipped — POST failed due to Content-Type rejection",
                    phase=phase,
                ))
                return results

    ok, errs = rv.validate_resource_response(
        resp.json() if resp.body else None,
        expected_status=201,
        actual_status=resp.status_code,
        headers=resp.headers,
        resource_type=resource_type,
    )
    results.extend(_validation_results(f"POST {endpoint}", phase, ok, errs))

    # Bail if the server didn't return an id — can't continue the lifecycle
    created = resp.json() if resp.body else None
    if not created or "id" not in (created or {}):
        results.append(ProbeResult(
            f"GET {endpoint}/{{id}}", ProbeResult.SKIP,
            message="No id returned from POST", phase=phase,
        ))
        return results

    resource_id = created["id"]
    created_resources.append({"endpoint": endpoint, "id": resource_id})

    # -- READ (GET by id) ---------------------------------------------------
    try:
        resp = client.get(f"{endpoint}/{resource_id}")
    except Exception as exc:
        results.append(ProbeResult(
            f"GET {endpoint}/{{id}}", ProbeResult.ERROR,
            message=str(exc), phase=phase,
        ))
        return results

    ok, errs = rv.validate_resource_response(
        resp.json() if resp.body else None,
        expected_status=200,
        actual_status=resp.status_code,
        headers=resp.headers,
        resource_type=resource_type,
    )
    results.extend(_validation_results(f"GET {endpoint}/{{id}}", phase, ok, errs))

    # -- UPDATE (PUT) -------------------------------------------------------
    new_display = f"Updated-{resource_id[:8]}"
    put_payload = dict(created)
    put_payload.pop("meta", None)  # Remove server-managed fields before PUT
    put_payload[display_name_field] = new_display

    try:
        resp = client.put(f"{endpoint}/{resource_id}", put_payload)
    except Exception as exc:
        results.append(ProbeResult(
            f"PUT {endpoint}/{{id}}", ProbeResult.ERROR,
            message=str(exc), phase=phase,
        ))
        return results

    ok, errs = rv.validate_resource_response(
        resp.json() if resp.body else None,
        expected_status=200,
        actual_status=resp.status_code,
        headers=resp.headers,
        resource_type=resource_type,
    )
    results.extend(_validation_results(f"PUT {endpoint}/{{id}}", phase, ok, errs))

    # Verify PUT took effect via a follow-up GET
    try:
        resp = client.get(f"{endpoint}/{resource_id}")
        body = resp.json() if resp.body else {}
        if body and body.get(display_name_field) == new_display:
            results.append(ProbeResult(
                f"GET {endpoint}/{{id}} after PUT", ProbeResult.PASS,
                message=f"{display_name_field} update persisted",
                phase=phase,
            ))
        else:
            actual = body.get(display_name_field) if body else None
            results.append(ProbeResult(
                f"GET {endpoint}/{{id}} after PUT", ProbeResult.FAIL,
                message=f"Expected {display_name_field}='{new_display}', got '{actual}'",
                phase=phase,
            ))
    except Exception as exc:
        results.append(ProbeResult(
            f"GET {endpoint}/{{id}} after PUT", ProbeResult.ERROR,
            message=str(exc), phase=phase,
        ))

    # -- PATCH (set active=false) -------------------------------------------
    patch_payload = make_patch([
        {"op": "replace", "path": "active", "value": False},
    ])
    try:
        resp = client.patch(f"{endpoint}/{resource_id}", patch_payload)
    except Exception as exc:
        results.append(ProbeResult(
            f"PATCH {endpoint}/{{id}}", ProbeResult.ERROR,
            message=str(exc), phase=phase,
        ))
        return results

    ok, errs = rv.validate_resource_response(
        resp.json() if resp.body else None,
        expected_status=200,
        actual_status=resp.status_code,
        headers=resp.headers,
        resource_type=resource_type,
    )
    results.extend(_validation_results(f"PATCH {endpoint}/{{id}}", phase, ok, errs))

    # Verify PATCH took effect via a follow-up GET.
    # active is not defined for Group resources (RFC 7643 §4.2), so for Groups
    # we only verify the GET succeeds rather than checking the active field.
    try:
        resp = client.get(f"{endpoint}/{resource_id}")
        body = resp.json() if resp.body else {}
        if resource_type == "Group":
            if resp.status_code == 200:
                results.append(ProbeResult(
                    f"GET {endpoint}/{{id}} after PATCH", ProbeResult.PASS,
                    message="200 OK confirmed",
                    phase=phase,
                ))
            else:
                results.append(ProbeResult(
                    f"GET {endpoint}/{{id}} after PATCH", ProbeResult.FAIL,
                    message=f"Expected 200, got {resp.status_code}", phase=phase,
                ))
        elif body and body.get("active") is False:
            results.append(ProbeResult(
                f"GET {endpoint}/{{id}} after PATCH", ProbeResult.PASS,
                message="active=false confirmed",
                phase=phase,
            ))
        else:
            results.append(ProbeResult(
                f"GET {endpoint}/{{id}} after PATCH", ProbeResult.FAIL,
                message=f"Expected active=false, got {body.get('active') if body else None}",
                phase=phase,
            ))
    except Exception as exc:
        results.append(ProbeResult(
            f"GET {endpoint}/{{id}} after PATCH", ProbeResult.ERROR,
            message=str(exc), phase=phase,
        ))

    # -- PATCH add + remove on multi-valued attribute (Groups only) ----------
    if resource_type == "Group":
        add_patch = make_patch([
            {"op": "add", "path": "members", "value": [{"value": "fake-member-id"}]},
        ])
        try:
            resp = client.patch(f"{endpoint}/{resource_id}", add_patch)
            if resp.status_code == 200:
                results.append(ProbeResult(
                    f"PATCH {endpoint}/{{id}} add member", ProbeResult.PASS, phase=phase,
                ))
            else:
                results.append(ProbeResult(
                    f"PATCH {endpoint}/{{id}} add member", ProbeResult.FAIL,
                    message=f"Expected 200, got {resp.status_code}", phase=phase,
                ))
        except Exception as exc:
            results.append(ProbeResult(
                f"PATCH {endpoint}/{{id}} add member", ProbeResult.ERROR,
                message=str(exc), phase=phase,
            ))

        rm_patch = make_patch([
            {"op": "remove", "path": "members"},
        ])
        try:
            resp = client.patch(f"{endpoint}/{resource_id}", rm_patch)
            if resp.status_code == 200:
                results.append(ProbeResult(
                    f"PATCH {endpoint}/{{id}} remove members", ProbeResult.PASS, phase=phase,
                ))
            else:
                results.append(ProbeResult(
                    f"PATCH {endpoint}/{{id}} remove members", ProbeResult.FAIL,
                    message=f"Expected 200, got {resp.status_code}", phase=phase,
                ))
        except Exception as exc:
            results.append(ProbeResult(
                f"PATCH {endpoint}/{{id}} remove members", ProbeResult.ERROR,
                message=str(exc), phase=phase,
            ))

    # -- DELETE -------------------------------------------------------------
    try:
        resp = client.delete(f"{endpoint}/{resource_id}")
    except Exception as exc:
        results.append(ProbeResult(
            f"DELETE {endpoint}/{{id}}", ProbeResult.ERROR,
            message=str(exc), phase=phase,
        ))
        return results

    ok, errs = rv.validate_delete_response(resp.status_code, body=resp.body)
    results.extend(_validation_results(f"DELETE {endpoint}/{{id}}", phase, ok, errs,
                                       pass_message="204 No Content"))
    if ok:
        # Already deleted — remove from cleanup list to avoid double-delete
        created_resources[:] = [
            r for r in created_resources if r["id"] != resource_id
        ]

    # Verify DELETE by confirming GET returns 404
    try:
        resp = client.get(f"{endpoint}/{resource_id}")
        if resp.status_code == 404:
            results.append(ProbeResult(
                f"GET {endpoint}/{{id}} after DELETE (expect 404)", ProbeResult.PASS,
                message="404 confirmed — resource no longer exists",
                phase=phase,
            ))
        else:
            results.append(ProbeResult(
                f"GET {endpoint}/{{id}} after DELETE (expect 404)", ProbeResult.FAIL,
                message=f"Expected 404, got {resp.status_code}", phase=phase,
            ))
    except Exception as exc:
        results.append(ProbeResult(
            f"GET {endpoint}/{{id}} after DELETE (expect 404)", ProbeResult.ERROR,
            message=str(exc), phase=phase,
        ))

    return results


# ---------------------------------------------------------------------------
# Phase 1: Discovery
# ---------------------------------------------------------------------------

def test_discovery(client: SCIMClient, rv: ServerResponseValidator) -> List[ProbeResult]:
    """Test the three SCIM discovery endpoints (RFC 7644 Section 4).

    Validates that each endpoint returns 200 with an appropriate Content-Type.
    In strict mode, ``application/json`` (instead of ``application/scim+json``)
    is reported as a warning.
    """
    results: List[ProbeResult] = []
    phase = "Phase 1 — Discovery"

    for path, name in [
        ("/ServiceProviderConfig", "GET /ServiceProviderConfig"),
        ("/Schemas", "GET /Schemas"),
        ("/ResourceTypes", "GET /ResourceTypes"),
    ]:
        try:
            resp = client.get(path)
        except Exception as exc:
            results.append(ProbeResult(name, ProbeResult.ERROR, message=str(exc), phase=phase))
            continue

        if resp.status_code == 200:
            ct = resp.header("Content-Type") or ""
            if "scim+json" in ct:
                results.append(ProbeResult(name, ProbeResult.PASS, phase=phase))
            elif "application/json" in ct:
                # Known deviation — pass but warn in strict mode
                results.append(ProbeResult(name, ProbeResult.PASS, phase=phase))
                if rv.strict:
                    results.append(ProbeResult(
                        name, ProbeResult.WARN,
                        message=f"Content-Type should be application/scim+json, got '{ct}'",
                        phase=phase,
                    ))
            else:
                results.append(ProbeResult(
                    name, ProbeResult.FAIL,
                    message=f"Content-Type should be application/scim+json, got '{ct}'",
                    phase=phase,
                ))
        else:
            results.append(ProbeResult(
                name, ProbeResult.FAIL,
                message=f"Expected 200, got {resp.status_code}", phase=phase,
            ))

    return results


def discover_supported_resources(client: SCIMClient) -> Set[str]:
    """Query /ResourceTypes to learn which resource types the server supports.

    Returns a set of resource type names (e.g. ``{"User", "Group", "Agent"}``).
    Falls back to ``{"User", "Group"}`` if /ResourceTypes is unavailable,
    since these are the two resource types required by RFC 7644.
    """
    try:
        resp = client.get("/ResourceTypes")
        if resp.status_code == 200 and resp.body:
            data = resp.json()
            # Response could be a ListResponse wrapper or a bare array
            resources = data if isinstance(data, list) else data.get("Resources", [])
            return {r["name"] for r in resources if "name" in r}
    except Exception:
        pass
    return {"User", "Group"}


# ---------------------------------------------------------------------------
# Phase 2-5: CRUD Lifecycles
# ---------------------------------------------------------------------------

def test_user_lifecycle(
    client: SCIMClient, rv: ServerResponseValidator,
    created_resources: List[Dict[str, Any]],
) -> List[ProbeResult]:
    """Phase 2 — Run a full CRUD lifecycle for User resources."""
    return _crud_lifecycle(
        client, rv, "User", "/Users", make_user,
        "Phase 2 — User CRUD Lifecycle", created_resources,
    )


def test_group_lifecycle(
    client: SCIMClient, rv: ServerResponseValidator,
    created_resources: List[Dict[str, Any]],
) -> List[ProbeResult]:
    """Phase 3 — Run a full CRUD lifecycle for Group resources.

    Includes additional PATCH tests for add/remove members.
    """
    return _crud_lifecycle(
        client, rv, "Group", "/Groups", make_group,
        "Phase 3 — Group CRUD Lifecycle", created_resources,
    )


def test_agent_lifecycle(
    client: SCIMClient, rv: ServerResponseValidator,
    created_resources: List[Dict[str, Any]],
) -> List[ProbeResult]:
    """Phase 4 — Run a full CRUD lifecycle for Agent resources.

    Per draft-abbey-scim-agent-extension-00.  Skipped by the runner
    if the server doesn't advertise Agent support.
    """
    return _crud_lifecycle(
        client, rv, "Agent", "/Agents", make_agent,
        "Phase 4 — Agent CRUD Lifecycle", created_resources,
        display_name_field="displayName",
    )


def test_agentic_application_lifecycle(
    client: SCIMClient, rv: ServerResponseValidator,
    created_resources: List[Dict[str, Any]],
) -> List[ProbeResult]:
    """Phase 5 — Run a full CRUD lifecycle for AgenticApplication resources."""
    return _crud_lifecycle(
        client, rv, "AgenticApplication", "/AgenticApplications",
        make_agentic_application,
        "Phase 5 — AgenticApplication CRUD Lifecycle", created_resources,
        display_name_field="displayName",
    )


# ---------------------------------------------------------------------------
# Phase 5a: Agent Rapid Lifecycle
# ---------------------------------------------------------------------------

def test_agent_rapid_lifecycle(
    client: SCIMClient, created_resources: List[Dict[str, Any]],
    count: int = 10,
) -> List[ProbeResult]:
    """Create and immediately delete multiple agents to test ephemeral provisioning.

    This exercises a real-world pattern where AI agents are created and
    destroyed at machine speed, unlike human JML lifecycles that span months.
    If a delete fails, the agent is added to ``created_resources`` for cleanup.
    """
    results: List[ProbeResult] = []
    phase = "Phase 5a — Agent Rapid Lifecycle"
    successes = 0
    failures = 0

    for i in range(count):
        try:
            payload = make_agent()
            resp = client.post("/Agents", payload)
            if resp.status_code != 201:
                failures += 1
                continue
            body = resp.json() if resp.body else None
            if not body or "id" not in body:
                failures += 1
                continue
            agent_id = body["id"]

            del_resp = client.delete(f"/Agents/{agent_id}")
            if del_resp.status_code == 204:
                successes += 1
            else:
                failures += 1
                # Track for cleanup since delete failed
                created_resources.append({"endpoint": "/Agents", "id": agent_id})
        except Exception:
            failures += 1

    if failures == 0:
        results.append(ProbeResult(
            f"Rapid create/delete {count} agents", ProbeResult.PASS,
            message=f"{successes}/{count} succeeded", phase=phase,
        ))
    else:
        results.append(ProbeResult(
            f"Rapid create/delete {count} agents", ProbeResult.FAIL,
            message=f"{successes}/{count} succeeded, {failures} failed", phase=phase,
        ))
    return results


# ---------------------------------------------------------------------------
# Phase 6: Search
# ---------------------------------------------------------------------------

def test_search(client: SCIMClient, rv: ServerResponseValidator) -> List[ProbeResult]:
    """Test list/search endpoints for ListResponse structure, filtering, and pagination."""
    results: List[ProbeResult] = []
    phase = "Phase 6 — Search"

    # -- Basic list (GET /Users) ---------------------------------------------
    try:
        resp = client.get("/Users")
        data = resp.json() if resp.body else None
        ok, errs = rv.validate_list_response(data, resp.status_code, resp.headers)
        results.extend(_validation_results("GET /Users (ListResponse)", phase, ok, errs))
    except Exception as exc:
        results.append(ProbeResult(
            "GET /Users (ListResponse)", ProbeResult.ERROR,
            message=str(exc), phase=phase,
        ))

    # -- Filter query (expect 0 results for non-existent user) ---------------
    try:
        # URL-encode the filter value to avoid urllib errors with spaces
        filter_val = urllib.parse.quote('userName eq "nonexistent@test.invalid"')
        resp = client.get(f'/Users?filter={filter_val}')
        data = resp.json() if resp.body else None
        if resp.status_code == 200 and data and data.get("totalResults", -1) == 0:
            results.append(ProbeResult(
                "GET /Users?filter (no match)", ProbeResult.PASS, phase=phase,
            ))
        elif resp.status_code == 200:
            # Server may ignore filters and return all resources
            results.append(ProbeResult(
                "GET /Users?filter (no match)", ProbeResult.PASS,
                message="Filter returned results (server may ignore filter)", phase=phase,
            ))
        elif resp.status_code == 400:
            # Some servers have partial filter support
            results.append(ProbeResult(
                "GET /Users?filter (no match)", ProbeResult.WARN,
                message="Server rejected filter with 400 (partial filter support)",
                phase=phase,
            ))
        else:
            results.append(ProbeResult(
                "GET /Users?filter (no match)", ProbeResult.FAIL,
                message=f"Expected 200, got {resp.status_code}", phase=phase,
            ))
    except Exception as exc:
        results.append(ProbeResult(
            "GET /Users?filter (no match)", ProbeResult.ERROR,
            message=str(exc), phase=phase,
        ))

    # -- Pagination (startIndex + count) -------------------------------------
    try:
        resp = client.get("/Users?startIndex=1&count=1")
        if resp.status_code == 200:
            data = resp.json() if resp.body else None
            results.append(ProbeResult(
                "GET /Users?startIndex=1&count=1", ProbeResult.PASS, phase=phase,
            ))
            # Check whether server honors the count parameter
            if data:
                if "itemsPerPage" in data:
                    if data["itemsPerPage"] > 1:
                        results.append(ProbeResult(
                            "Pagination: itemsPerPage honors count", ProbeResult.WARN,
                            message=f"Requested count=1 but itemsPerPage={data['itemsPerPage']}",
                            phase=phase,
                        ))
        else:
            results.append(ProbeResult(
                "GET /Users?startIndex=1&count=1", ProbeResult.FAIL,
                message=f"Expected 200, got {resp.status_code}", phase=phase,
            ))
    except Exception as exc:
        results.append(ProbeResult(
            "GET /Users?startIndex=1&count=1", ProbeResult.ERROR,
            message=str(exc), phase=phase,
        ))

    # -- Boundary case: count=0 should return no Resources -------------------
    try:
        resp = client.get("/Users?count=0")
        if resp.status_code == 200:
            data = resp.json() if resp.body else None
            if data and isinstance(data.get("Resources"), list) and len(data["Resources"]) == 0:
                results.append(ProbeResult(
                    "GET /Users?count=0 (boundary)", ProbeResult.PASS, phase=phase,
                ))
            else:
                results.append(ProbeResult(
                    "GET /Users?count=0 (boundary)", ProbeResult.WARN,
                    message="count=0 should return no Resources",
                    phase=phase,
                ))
        else:
            results.append(ProbeResult(
                "GET /Users?count=0 (boundary)", ProbeResult.WARN,
                message=f"Expected 200, got {resp.status_code}", phase=phase,
            ))
    except Exception as exc:
        results.append(ProbeResult(
            "GET /Users?count=0 (boundary)", ProbeResult.ERROR,
            message=str(exc), phase=phase,
        ))

    return results


# ---------------------------------------------------------------------------
# Phase 7: Error Handling
# ---------------------------------------------------------------------------

def test_error_handling(client: SCIMClient, rv: ServerResponseValidator) -> List[ProbeResult]:
    """Test that the server returns proper SCIM error responses.

    Verifies:
    - GET nonexistent resource returns 404 with SCIM error schema
    - POST with invalid body (no schemas) returns 400
    - POST with missing required attribute returns 400
    """
    results: List[ProbeResult] = []
    phase = "Phase 7 — Error Handling"

    # -- GET nonexistent resource (expect 404) -------------------------------
    try:
        resp = client.get("/Users/nonexistent-id-000000")
        data = resp.json() if resp.body else None
        ok, errs = rv.validate_error_response(data, 404, resp.status_code)
        results.extend(_validation_results(
            "GET /Users/nonexistent (expect 404)", phase, ok, errs,
        ))
    except Exception as exc:
        results.append(ProbeResult(
            "GET /Users/nonexistent (expect 404)", ProbeResult.ERROR,
            message=str(exc), phase=phase,
        ))

    # -- POST invalid body (expect 400) --------------------------------------
    try:
        resp = client.post("/Users", {"not": "a scim resource"})
        data = resp.json() if resp.body else None
        ok, errs = rv.validate_error_response(data, 400, resp.status_code)
        results.extend(_validation_results(
            "POST /Users invalid body (expect 400)", phase, ok, errs,
        ))
    except Exception as exc:
        results.append(ProbeResult(
            "POST /Users invalid body (expect 400)", ProbeResult.ERROR,
            message=str(exc), phase=phase,
        ))

    # -- POST missing required field (expect 400) ----------------------------
    try:
        resp = client.post("/Users", {
            "schemas": ["urn:ietf:params:scim:schemas:core:2.0:User"],
            # userName intentionally omitted
        })
        data = resp.json() if resp.body else None
        ok, errs = rv.validate_error_response(data, 400, resp.status_code)
        results.extend(_validation_results(
            "POST /Users missing userName (expect 400)", phase, ok, errs,
        ))
    except Exception as exc:
        results.append(ProbeResult(
            "POST /Users missing userName (expect 400)", ProbeResult.ERROR,
            message=str(exc), phase=phase,
        ))

    return results
