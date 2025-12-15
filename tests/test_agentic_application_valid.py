"""Tests for valid AgenticApplication resources."""

import pytest
from scim_sanity.validator import SCIMValidator


def test_valid_minimal_agentic_application():
    """Test a minimal valid AgenticApplication resource."""
    data = {
        "schemas": ["urn:ietf:params:scim:schemas:core:2.0:AgenticApplication"],
        "name": "my-agentic-app"
    }
    validator = SCIMValidator()
    is_valid, errors = validator.validate(data)
    assert is_valid, f"Expected valid, got errors: {errors}"


def test_valid_agentic_application_with_display_name():
    """Test an AgenticApplication resource with displayName."""
    data = {
        "schemas": ["urn:ietf:params:scim:schemas:core:2.0:AgenticApplication"],
        "name": "assistant-platform",
        "displayName": "Assistant Platform"
    }
    validator = SCIMValidator()
    is_valid, errors = validator.validate(data)
    assert is_valid, f"Expected valid, got errors: {errors}"


def test_valid_full_agentic_application():
    """Test a fully populated valid AgenticApplication resource."""
    data = {
        "schemas": ["urn:ietf:params:scim:schemas:core:2.0:AgenticApplication"],
        "name": "research-platform",
        "displayName": "Research Platform",
        "description": "A platform for AI research agents",
        "active": True,
        "externalId": "ext-app-001"
    }
    validator = SCIMValidator()
    is_valid, errors = validator.validate(data)
    assert is_valid, f"Expected valid, got errors: {errors}"
