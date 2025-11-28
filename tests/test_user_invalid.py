"""Tests for invalid User resources."""

import pytest
from scim_sanity.validator import SCIMValidator


def test_user_missing_userName():
    """Test User resource missing required userName."""
    data = {
        "schemas": ["urn:ietf:params:scim:schemas:core:2.0:User"]
    }
    validator = SCIMValidator()
    is_valid, errors = validator.validate(data)
    assert not is_valid
    assert any("userName" in str(e).lower() for e in errors)


def test_user_missing_schemas():
    """Test User resource missing schemas field."""
    data = {
        "userName": "user@example.com"
    }
    validator = SCIMValidator()
    is_valid, errors = validator.validate(data)
    assert not is_valid
    assert any("schemas" in str(e).lower() for e in errors)


def test_user_invalid_schema_urn():
    """Test User resource with invalid schema URN."""
    data = {
        "schemas": ["invalid:schema:urn"],
        "userName": "user@example.com"
    }
    validator = SCIMValidator()
    is_valid, errors = validator.validate(data)
    assert not is_valid
    assert any("unknown schema" in str(e).lower() or "invalid schema" in str(e).lower() for e in errors)


def test_user_immutable_id_set():
    """Test User resource trying to set immutable id attribute."""
    data = {
        "schemas": ["urn:ietf:params:scim:schemas:core:2.0:User"],
        "userName": "user@example.com",
        "id": "should-not-be-set"
    }
    validator = SCIMValidator()
    is_valid, errors = validator.validate(data)
    assert not is_valid
    assert any("immutable" in str(e).lower() or "readOnly" in str(e).lower() for e in errors)


def test_user_null_value():
    """Test User resource with null value (should use PATCH remove instead)."""
    data = {
        "schemas": ["urn:ietf:params:scim:schemas:core:2.0:User"],
        "userName": "user@example.com",
        "displayName": None
    }
    validator = SCIMValidator()
    is_valid, errors = validator.validate(data)
    assert not is_valid
    assert any("null" in str(e).lower() for e in errors)


def test_user_invalid_emails_structure():
    """Test User resource with invalid emails structure (not an array)."""
    data = {
        "schemas": ["urn:ietf:params:scim:schemas:core:2.0:User"],
        "userName": "user@example.com",
        "emails": "not-an-array"
    }
    validator = SCIMValidator()
    is_valid, errors = validator.validate(data)
    assert not is_valid
    assert any("array" in str(e).lower() or "multivalued" in str(e).lower() for e in errors)

