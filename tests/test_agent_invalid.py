"""Tests for invalid Agent resources."""

import pytest
from scim_sanity.validator import SCIMValidator


def test_agent_missing_required_name():
    """Test Agent resource missing required 'name' attribute."""
    data = {
        "schemas": ["urn:ietf:params:scim:schemas:core:2.0:Agent"]
    }
    validator = SCIMValidator()
    is_valid, errors = validator.validate(data)
    assert not is_valid
    assert any("name" in str(e).lower() and "required" in str(e).lower() for e in errors)


def test_agent_empty_name():
    """Test Agent resource with empty 'name' attribute."""
    data = {
        "schemas": ["urn:ietf:params:scim:schemas:core:2.0:Agent"],
        "name": ""
    }
    validator = SCIMValidator()
    is_valid, errors = validator.validate(data)
    assert not is_valid
    assert any("name" in str(e).lower() and "non-empty" in str(e).lower() for e in errors)


def test_agent_invalid_schema_urn():
    """Test Agent resource with invalid schema URN."""
    data = {
        "schemas": ["invalid:schema:urn"],
        "name": "test-agent"
    }
    validator = SCIMValidator()
    is_valid, errors = validator.validate(data)
    assert not is_valid
    assert any("invalid schema" in str(e).lower() or "unknown schema" in str(e).lower() for e in errors)


def test_agent_immutable_id_set():
    """Test Agent resource trying to set immutable id attribute."""
    data = {
        "schemas": ["urn:ietf:params:scim:schemas:core:2.0:Agent"],
        "name": "test-agent",
        "id": "12345"
    }
    validator = SCIMValidator()
    is_valid, errors = validator.validate(data)
    assert not is_valid
    assert any("immutable" in str(e).lower() or "readonly" in str(e).lower() for e in errors)


def test_agent_null_value():
    """Test Agent resource with null value (should use PATCH remove instead)."""
    data = {
        "schemas": ["urn:ietf:params:scim:schemas:core:2.0:Agent"],
        "name": "test-agent",
        "displayName": None
    }
    validator = SCIMValidator()
    is_valid, errors = validator.validate(data)
    assert not is_valid
    assert any("null" in str(e).lower() for e in errors)
