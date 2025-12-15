"""Tests for valid Agent resources."""

import pytest
from scim_sanity.validator import SCIMValidator


def test_valid_minimal_agent():
    """Test a minimal valid Agent resource."""
    data = {
        "schemas": ["urn:ietf:params:scim:schemas:core:2.0:Agent"],
        "name": "Clippy 2.0"
    }
    validator = SCIMValidator()
    is_valid, errors = validator.validate(data)
    assert is_valid, f"Expected valid, got errors: {errors}"


def test_valid_agent_with_display_name():
    """Test an Agent resource with displayName."""
    data = {
        "schemas": ["urn:ietf:params:scim:schemas:core:2.0:Agent"],
        "name": "helpdesk-bot",
        "displayName": "Helpdesk Bot"
    }
    validator = SCIMValidator()
    is_valid, errors = validator.validate(data)
    assert is_valid, f"Expected valid, got errors: {errors}"


def test_valid_full_agent():
    """Test a fully populated valid Agent resource."""
    data = {
        "schemas": ["urn:ietf:params:scim:schemas:core:2.0:Agent"],
        "name": "research-assistant",
        "displayName": "Research Assistant",
        "agentType": "Assistant",
        "active": True,
        "description": "An AI research assistant agent",
        "externalId": "ext-agent-001"
    }
    validator = SCIMValidator()
    is_valid, errors = validator.validate(data)
    assert is_valid, f"Expected valid, got errors: {errors}"


def test_valid_agent_with_attributes():
    """Test an Agent resource with optional attributes."""
    data = {
        "schemas": ["urn:ietf:params:scim:schemas:core:2.0:Agent"],
        "name": "chatbot-agent",
        "agentType": "Chat bot",
        "active": True,
        "entitlements": [
            {
                "value": "read:documents",
                "display": "Read Documents",
                "type": "permission"
            }
        ],
        "roles": [
            {
                "value": "assistant",
                "display": "Assistant Role",
                "primary": True
            }
        ]
    }
    validator = SCIMValidator()
    is_valid, errors = validator.validate(data)
    assert is_valid, f"Expected valid, got errors: {errors}"
