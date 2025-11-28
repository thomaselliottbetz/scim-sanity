"""Tests for valid Group resources."""

import pytest
from scim_sanity.validator import SCIMValidator


def test_valid_minimal_group():
    """Test a minimal valid Group resource."""
    data = {
        "schemas": ["urn:ietf:params:scim:schemas:core:2.0:Group"],
        "displayName": "Engineering Team"
    }
    validator = SCIMValidator()
    is_valid, errors = validator.validate(data)
    assert is_valid, f"Expected valid, got errors: {errors}"


def test_valid_group_with_members():
    """Test a Group resource with members."""
    data = {
        "schemas": ["urn:ietf:params:scim:schemas:core:2.0:Group"],
        "displayName": "Developers",
        "members": [
            {
                "value": "user-id-1",
                "display": "John Doe",
                "type": "User"
            },
            {
                "value": "user-id-2",
                "display": "Jane Smith",
                "type": "User"
            }
        ],
        "externalId": "group-ext-123"
    }
    validator = SCIMValidator()
    is_valid, errors = validator.validate(data)
    assert is_valid, f"Expected valid, got errors: {errors}"


def test_valid_empty_group():
    """Test a Group resource with no members (empty group)."""
    data = {
        "schemas": ["urn:ietf:params:scim:schemas:core:2.0:Group"],
        "displayName": "New Group",
        "members": []
    }
    validator = SCIMValidator()
    is_valid, errors = validator.validate(data)
    assert is_valid, f"Expected valid, got errors: {errors}"

