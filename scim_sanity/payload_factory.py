"""Generates valid SCIM payloads for probe testing.

Each factory function produces a minimal, spec-compliant SCIM resource
with UUID-based unique values.  All generated values use the
``scim-sanity-test-`` prefix for namespace isolation so test resources
are easily identifiable and won't collide with real data on a live server.

These payloads are also validated by the existing ``SCIMValidator`` in
``test_payload_factory.py`` to ensure they remain correct as schemas evolve.
"""

import uuid
from typing import Any, Dict, Optional


def _unique_suffix() -> str:
    """Generate an 8-character hex suffix for unique test values."""
    return uuid.uuid4().hex[:8]


def make_user(extra: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
    """Generate a minimal valid User payload with unique userName and email.

    Includes ``name``, ``displayName``, ``active``, and ``emails`` to exercise
    common server-side attribute handling during the CRUD lifecycle.
    """
    suffix = _unique_suffix()
    payload: Dict[str, Any] = {
        "schemas": ["urn:ietf:params:scim:schemas:core:2.0:User"],
        "userName": f"scim-sanity-test-{suffix}@example.com",
        "name": {
            "givenName": "SCIMSanity",
            "familyName": f"Test-{suffix}",
        },
        "displayName": f"SCIM Sanity Test User {suffix}",
        "active": True,
        "emails": [
            {
                "value": f"scim-sanity-test-{suffix}@example.com",
                "type": "work",
                "primary": True,
            }
        ],
    }
    if extra:
        payload.update(extra)
    return payload


def make_group(
    members: Optional[list] = None, extra: Optional[Dict[str, Any]] = None
) -> Dict[str, Any]:
    """Generate a minimal valid Group payload with unique displayName."""
    suffix = _unique_suffix()
    payload: Dict[str, Any] = {
        "schemas": ["urn:ietf:params:scim:schemas:core:2.0:Group"],
        "displayName": f"scim-sanity-test-group-{suffix}",
    }
    if members:
        payload["members"] = members
    if extra:
        payload.update(extra)
    return payload


def make_agent(extra: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
    """Generate a minimal valid Agent payload per draft-abbey-scim-agent-extension-00.

    Includes ``displayName`` and ``active`` beyond the required ``name`` to
    exercise common attribute handling.
    """
    suffix = _unique_suffix()
    payload: Dict[str, Any] = {
        "schemas": ["urn:ietf:params:scim:schemas:core:2.0:Agent"],
        "name": f"scim-sanity-test-agent-{suffix}",
        "displayName": f"SCIM Sanity Test Agent {suffix}",
        "active": True,
    }
    if extra:
        payload.update(extra)
    return payload


def make_agentic_application(extra: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
    """Generate a minimal valid AgenticApplication payload."""
    suffix = _unique_suffix()
    payload: Dict[str, Any] = {
        "schemas": ["urn:ietf:params:scim:schemas:core:2.0:AgenticApplication"],
        "name": f"scim-sanity-test-app-{suffix}",
        "displayName": f"SCIM Sanity Test App {suffix}",
        "active": True,
    }
    if extra:
        payload.update(extra)
    return payload


def make_patch(operations: list) -> Dict[str, Any]:
    """Generate a SCIM PatchOp payload wrapping the given operations list."""
    return {
        "schemas": ["urn:ietf:params:scim:api:messages:2.0:PatchOp"],
        "Operations": operations,
    }


def update_user_display_name(original: Dict[str, Any], new_name: str) -> Dict[str, Any]:
    """Return a shallow copy of a user payload with ``displayName`` changed.

    Used for PUT testing — the original payload is not mutated.
    """
    updated = dict(original)
    updated["displayName"] = new_name
    return updated
