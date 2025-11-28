"""Tests for valid PATCH operations."""

import pytest
from scim_sanity.validator import SCIMValidator


def test_valid_patch_add():
    """Test a valid PATCH add operation."""
    data = {
        "schemas": ["urn:ietf:params:scim:api:messages:2.0:PatchOp"],
        "Operations": [
            {
                "op": "add",
                "path": "emails",
                "value": [
                    {
                        "value": "newemail@example.com",
                        "type": "work",
                        "primary": False
                    }
                ]
            }
        ]
    }
    validator = SCIMValidator()
    is_valid, errors = validator.validate(data, operation="patch")
    assert is_valid, f"Expected valid, got errors: {errors}"


def test_valid_patch_replace():
    """Test a valid PATCH replace operation."""
    data = {
        "schemas": ["urn:ietf:params:scim:api:messages:2.0:PatchOp"],
        "Operations": [
            {
                "op": "replace",
                "path": "displayName",
                "value": "New Display Name"
            }
        ]
    }
    validator = SCIMValidator()
    is_valid, errors = validator.validate(data, operation="patch")
    assert is_valid, f"Expected valid, got errors: {errors}"


def test_valid_patch_remove():
    """Test a valid PATCH remove operation."""
    data = {
        "schemas": ["urn:ietf:params:scim:api:messages:2.0:PatchOp"],
        "Operations": [
            {
                "op": "remove",
                "path": "emails[type eq \"work\"]"
            }
        ]
    }
    validator = SCIMValidator()
    is_valid, errors = validator.validate(data, operation="patch")
    assert is_valid, f"Expected valid, got errors: {errors}"


def test_valid_patch_multiple_operations():
    """Test a valid PATCH with multiple operations."""
    data = {
        "schemas": ["urn:ietf:params:scim:api:messages:2.0:PatchOp"],
        "Operations": [
            {
                "op": "replace",
                "path": "displayName",
                "value": "Updated Name"
            },
            {
                "op": "add",
                "path": "emails",
                "value": [
                    {
                        "value": "new@example.com",
                        "type": "work"
                    }
                ]
            },
            {
                "op": "remove",
                "path": "nickName"
            }
        ]
    }
    validator = SCIMValidator()
    is_valid, errors = validator.validate(data, operation="patch")
    assert is_valid, f"Expected valid, got errors: {errors}"

