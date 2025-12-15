"""Tests for invalid AgenticApplication resources."""

import pytest
from scim_sanity.validator import SCIMValidator


def test_agentic_application_missing_required_name():
    """Test AgenticApplication resource missing required 'name' attribute."""
    data = {
        "schemas": ["urn:ietf:params:scim:schemas:core:2.0:AgenticApplication"]
    }
    validator = SCIMValidator()
    is_valid, errors = validator.validate(data)
    assert not is_valid
    assert any("name" in str(e).lower() and "required" in str(e).lower() for e in errors)


def test_agentic_application_empty_name():
    """Test AgenticApplication resource with empty 'name' attribute."""
    data = {
        "schemas": ["urn:ietf:params:scim:schemas:core:2.0:AgenticApplication"],
        "name": ""
    }
    validator = SCIMValidator()
    is_valid, errors = validator.validate(data)
    assert not is_valid
    assert any("name" in str(e).lower() and "non-empty" in str(e).lower() for e in errors)


def test_agentic_application_invalid_schema_urn():
    """Test AgenticApplication resource with invalid schema URN."""
    data = {
        "schemas": ["invalid:schema:urn"],
        "name": "test-app"
    }
    validator = SCIMValidator()
    is_valid, errors = validator.validate(data)
    assert not is_valid
    assert any("invalid schema" in str(e).lower() or "unknown schema" in str(e).lower() for e in errors)
