"""Tests for valid User resources."""

import pytest
from scim_sanity.validator import SCIMValidator


def test_valid_minimal_user():
    """Test a minimal valid User resource."""
    data = {
        "schemas": ["urn:ietf:params:scim:schemas:core:2.0:User"],
        "userName": "john.doe@example.com"
    }
    validator = SCIMValidator()
    is_valid, errors = validator.validate(data)
    assert is_valid, f"Expected valid, got errors: {errors}"


def test_valid_full_user():
    """Test a fully populated valid User resource."""
    data = {
        "schemas": ["urn:ietf:params:scim:schemas:core:2.0:User"],
        "userName": "jane.smith@example.com",
        "name": {
            "givenName": "Jane",
            "familyName": "Smith",
            "formatted": "Jane Smith"
        },
        "displayName": "Jane Smith",
        "emails": [
            {
                "value": "jane.smith@example.com",
                "type": "work",
                "primary": True
            }
        ],
        "active": True,
        "externalId": "ext-12345"
    }
    validator = SCIMValidator()
    is_valid, errors = validator.validate(data)
    assert is_valid, f"Expected valid, got errors: {errors}"


def test_valid_user_with_enterprise_extension():
    """Test a User resource with enterprise extension."""
    data = {
        "schemas": [
            "urn:ietf:params:scim:schemas:core:2.0:User",
            "urn:ietf:params:scim:schemas:extension:enterprise:2.0:User"
        ],
        "userName": "manager@example.com",
        "urn:ietf:params:scim:schemas:extension:enterprise:2.0:User": {
            "employeeNumber": "EMP-001",
            "department": "Engineering",
            "manager": {
                "value": "ceo-id",
                "displayName": "CEO"
            }
        }
    }
    validator = SCIMValidator()
    is_valid, errors = validator.validate(data)
    assert is_valid, f"Expected valid, got errors: {errors}"


def test_valid_user_with_multiple_emails():
    """Test a User resource with multiple email addresses."""
    data = {
        "schemas": ["urn:ietf:params:scim:schemas:core:2.0:User"],
        "userName": "user@example.com",
        "emails": [
            {
                "value": "work@example.com",
                "type": "work",
                "primary": True
            },
            {
                "value": "personal@example.com",
                "type": "home",
                "primary": False
            }
        ]
    }
    validator = SCIMValidator()
    is_valid, errors = validator.validate(data)
    assert is_valid, f"Expected valid, got errors: {errors}"

