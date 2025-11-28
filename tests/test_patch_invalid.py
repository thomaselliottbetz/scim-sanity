"""Tests for invalid PATCH operations."""

import pytest
from scim_sanity.validator import SCIMValidator


def test_patch_missing_operations():
    """Test PATCH operation missing Operations array."""
    data = {
        "schemas": ["urn:ietf:params:scim:api:messages:2.0:PatchOp"]
    }
    validator = SCIMValidator()
    is_valid, errors = validator.validate(data, operation="patch")
    assert not is_valid
    assert any("operations" in str(e).lower() for e in errors)


def test_patch_invalid_op_value():
    """Test PATCH operation with invalid 'op' value."""
    data = {
        "schemas": ["urn:ietf:params:scim:api:messages:2.0:PatchOp"],
        "Operations": [
            {
                "op": "invalid",
                "path": "displayName",
                "value": "test"
            }
        ]
    }
    validator = SCIMValidator()
    is_valid, errors = validator.validate(data, operation="patch")
    assert not is_valid
    assert any("invalid 'op'" in str(e).lower() for e in errors)


def test_patch_remove_missing_path():
    """Test PATCH remove operation missing required path."""
    data = {
        "schemas": ["urn:ietf:params:scim:api:messages:2.0:PatchOp"],
        "Operations": [
            {
                "op": "remove"
            }
        ]
    }
    validator = SCIMValidator()
    is_valid, errors = validator.validate(data, operation="patch")
    assert not is_valid
    assert any("path" in str(e).lower() and "remove" in str(e).lower() for e in errors)


def test_patch_add_missing_value():
    """Test PATCH add operation missing required value."""
    data = {
        "schemas": ["urn:ietf:params:scim:api:messages:2.0:PatchOp"],
        "Operations": [
            {
                "op": "add",
                "path": "displayName"
            }
        ]
    }
    validator = SCIMValidator()
    is_valid, errors = validator.validate(data, operation="patch")
    assert not is_valid
    assert any("value" in str(e).lower() and "add" in str(e).lower() for e in errors)


def test_patch_duplicate_paths():
    """Test PATCH operation with duplicate paths."""
    data = {
        "schemas": ["urn:ietf:params:scim:api:messages:2.0:PatchOp"],
        "Operations": [
            {
                "op": "replace",
                "path": "displayName",
                "value": "First"
            },
            {
                "op": "replace",
                "path": "displayName",
                "value": "Second"
            }
        ]
    }
    validator = SCIMValidator()
    is_valid, errors = validator.validate(data, operation="patch")
    assert not is_valid
    assert any("duplicate" in str(e).lower() and "path" in str(e).lower() for e in errors)


def test_patch_empty_operations():
    """Test PATCH operation with empty Operations array."""
    data = {
        "schemas": ["urn:ietf:params:scim:api:messages:2.0:PatchOp"],
        "Operations": []
    }
    validator = SCIMValidator()
    is_valid, errors = validator.validate(data, operation="patch")
    assert not is_valid
    assert any("empty" in str(e).lower() or "cannot be empty" in str(e).lower() for e in errors)


def test_patch_missing_patchop_schema():
    """Test PATCH operation missing PatchOp schema."""
    data = {
        "schemas": ["urn:ietf:params:scim:schemas:core:2.0:User"],
        "Operations": [
            {
                "op": "replace",
                "path": "displayName",
                "value": "test"
            }
        ]
    }
    validator = SCIMValidator()
    is_valid, errors = validator.validate(data, operation="patch")
    assert not is_valid
    assert any("patchop" in str(e).lower() for e in errors)

