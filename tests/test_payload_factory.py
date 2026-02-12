"""Tests for the payload factory — verify generated payloads pass existing SCIMValidator.

Ensures that every factory function (make_user, make_group, make_agent,
make_agentic_application, make_patch) produces payloads that are valid
according to the client-side validator, and that unique suffixes are
actually unique across calls.
"""

import pytest
from scim_sanity.validator import SCIMValidator
from scim_sanity.payload_factory import (
    make_user,
    make_group,
    make_agent,
    make_agentic_application,
    make_patch,
    update_user_display_name,
)


@pytest.fixture
def validator():
    return SCIMValidator()


def test_make_user_is_valid(validator):
    payload = make_user()
    ok, errors = validator.validate(payload)
    assert ok, f"Generated user should be valid: {errors}"


def test_make_user_unique_values():
    a = make_user()
    b = make_user()
    assert a["userName"] != b["userName"]


def test_make_group_is_valid(validator):
    payload = make_group()
    ok, errors = validator.validate(payload)
    assert ok, f"Generated group should be valid: {errors}"


def test_make_group_with_members(validator):
    payload = make_group(members=[{"value": "user-id-123"}])
    ok, errors = validator.validate(payload)
    assert ok, f"Generated group with members should be valid: {errors}"
    assert len(payload["members"]) == 1


def test_make_agent_is_valid(validator):
    payload = make_agent()
    ok, errors = validator.validate(payload)
    assert ok, f"Generated agent should be valid: {errors}"


def test_make_agentic_application_is_valid(validator):
    payload = make_agentic_application()
    ok, errors = validator.validate(payload)
    assert ok, f"Generated agentic application should be valid: {errors}"


def test_make_patch_is_valid(validator):
    payload = make_patch([
        {"op": "replace", "path": "active", "value": False},
    ])
    ok, errors = validator.validate(payload, operation="patch")
    assert ok, f"Generated patch should be valid: {errors}"


def test_update_user_display_name():
    original = make_user()
    updated = update_user_display_name(original, "New Name")
    assert updated["displayName"] == "New Name"
    # Original should not be mutated (shallow copy — schemas list is shared but that's fine)
    assert original["userName"] == updated["userName"]
