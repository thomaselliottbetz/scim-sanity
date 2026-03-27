"""Curated SCIM example payload catalog.

Each entry has the following fields:
  id            Unique slug, used as URL param for "Load in Validator"
  name          Short human-readable name
  description   One-sentence description
  resource_type "User" | "Group" | "Agent" | "AgenticApplication" | "PATCH"
  operation     "full" (POST/PUT) | "patch" (PATCH)
  valid         True if the payload should pass validation
  rfc_notes     RFC citation and key rule being demonstrated
  payload       The SCIM JSON payload dict
  expected_errors  (internal, not in API response) substrings that must appear
                   in error messages when valid=False. Used by the test suite.
"""

from typing import Any, Dict, List

EXAMPLES: List[Dict[str, Any]] = [
    # ------------------------------------------------------------------
    # Valid examples
    # ------------------------------------------------------------------
    {
        "id": "user-minimal",
        "name": "Minimal User",
        "description": "Smallest valid User payload — just schemas and userName.",
        "resource_type": "User",
        "operation": "full",
        "valid": True,
        "rfc_notes": "userName is the only required attribute (RFC 7643 §4.1)",
        "payload": {
            "schemas": ["urn:ietf:params:scim:schemas:core:2.0:User"],
            "userName": "john.doe@example.com",
        },
    },
    {
        "id": "user-full",
        "name": "Full User",
        "description": (
            "User with name, displayName, emails, phoneNumbers, addresses, and active. "
            "Shows multi-valued complex attributes with primary flag."
        ),
        "resource_type": "User",
        "operation": "full",
        "valid": True,
        "rfc_notes": "Multi-valued complex attributes with primary flag (RFC 7643 §4.1, §2.4)",
        "payload": {
            "schemas": ["urn:ietf:params:scim:schemas:core:2.0:User"],
            "userName": "jane.smith@example.com",
            "displayName": "Jane Smith",
            "name": {
                "formatted": "Ms. Jane Smith",
                "familyName": "Smith",
                "givenName": "Jane",
            },
            "emails": [
                {"value": "jane.smith@example.com", "type": "work", "primary": True},
                {"value": "jane@personal.example.com", "type": "personal"},
            ],
            "phoneNumbers": [
                {"value": "+1-206-555-0100", "type": "work", "primary": True},
            ],
            "addresses": [
                {
                    "streetAddress": "100 Universal City Plaza",
                    "locality": "Hollywood",
                    "region": "CA",
                    "postalCode": "91608",
                    "country": "US",
                    "type": "work",
                    "primary": True,
                }
            ],
            "active": True,
        },
    },
    {
        "id": "user-enterprise",
        "name": "Enterprise User",
        "description": (
            "User with enterprise extension — employeeNumber, department, manager. "
            "Shows extension schema URN in schemas array and as a top-level key."
        ),
        "resource_type": "User",
        "operation": "full",
        "valid": True,
        "rfc_notes": (
            "Extension attributes nested under the schema URN key (RFC 7643 §4.3)"
        ),
        "payload": {
            "schemas": [
                "urn:ietf:params:scim:schemas:core:2.0:User",
                "urn:ietf:params:scim:schemas:extension:enterprise:2.0:User",
            ],
            "userName": "bjensen@example.com",
            "displayName": "Babs Jensen",
            "urn:ietf:params:scim:schemas:extension:enterprise:2.0:User": {
                "employeeNumber": "701984",
                "department": "Tour Operations",
                "manager": {
                    "value": "26118915-6090-4610-87e4-49d8ca9f808d",
                    "displayName": "John Smith",
                },
            },
        },
    },
    {
        "id": "group-minimal",
        "name": "Minimal Group",
        "description": "Smallest valid Group payload — just schemas and displayName.",
        "resource_type": "Group",
        "operation": "full",
        "valid": True,
        "rfc_notes": "displayName is the only required attribute (RFC 7643 §4.2)",
        "payload": {
            "schemas": ["urn:ietf:params:scim:schemas:core:2.0:Group"],
            "displayName": "Engineering",
        },
    },
    {
        "id": "group-with-members",
        "name": "Group with Members",
        "description": "Group with a members array containing value, display, and type.",
        "resource_type": "Group",
        "operation": "full",
        "valid": True,
        "rfc_notes": "members multi-valued complex attribute (RFC 7643 §4.2, §2.4)",
        "payload": {
            "schemas": ["urn:ietf:params:scim:schemas:core:2.0:Group"],
            "displayName": "Tour Guides",
            "members": [
                {
                    "value": "2819c223-7f76-453a-919d-413861904646",
                    "display": "Babs Jensen",
                    "type": "User",
                },
                {
                    "value": "902c246b-6245-4190-8e05-00816be7344a",
                    "display": "Mandy Pepperidge",
                    "type": "User",
                },
            ],
        },
    },
    {
        "id": "agent-minimal",
        "name": "Minimal Agent",
        "description": "Smallest valid Agent payload — just schemas and name.",
        "resource_type": "Agent",
        "operation": "full",
        "valid": True,
        "rfc_notes": (
            "name is the only required attribute "
            "(draft-abbey-scim-agent-extension-00 §5.1.4)"
        ),
        "payload": {
            "schemas": ["urn:ietf:params:scim:schemas:core:2.0:Agent"],
            "name": "research-agent",
        },
    },
    {
        "id": "agent-full",
        "name": "Full Agent",
        "description": "Agent with displayName, agentType, active, and description.",
        "resource_type": "Agent",
        "operation": "full",
        "valid": True,
        "rfc_notes": "Agent optional attributes (draft-abbey-scim-agent-extension-00 §5.1)",
        "payload": {
            "schemas": ["urn:ietf:params:scim:schemas:core:2.0:Agent"],
            "name": "customer-support-agent",
            "displayName": "Customer Support Agent",
            "agentType": "Assistant",
            "active": True,
            "description": "Handles tier-1 customer support inquiries via chat.",
        },
    },
    {
        "id": "agentic-application-minimal",
        "name": "Minimal AgenticApplication",
        "description": "Smallest valid AgenticApplication — just schemas and name.",
        "resource_type": "AgenticApplication",
        "operation": "full",
        "valid": True,
        "rfc_notes": (
            "name is the only required attribute "
            "(draft-abbey-scim-agent-extension-00 §5.2.4)"
        ),
        "payload": {
            "schemas": ["urn:ietf:params:scim:schemas:core:2.0:AgenticApplication"],
            "name": "support-platform",
        },
    },
    {
        "id": "patch-replace",
        "name": "PATCH — Replace",
        "description": "PATCH replacing displayName. Single replace operation.",
        "resource_type": "PATCH",
        "operation": "patch",
        "valid": True,
        "rfc_notes": "PATCH replace operation (RFC 7644 §3.5.2)",
        "payload": {
            "schemas": ["urn:ietf:params:scim:api:messages:2.0:PatchOp"],
            "Operations": [
                {
                    "op": "replace",
                    "path": "displayName",
                    "value": "Updated Display Name",
                }
            ],
        },
    },
    {
        "id": "patch-multi-op",
        "name": "PATCH — Multiple Operations",
        "description": "PATCH with add, replace, and remove operations in one request.",
        "resource_type": "PATCH",
        "operation": "patch",
        "valid": True,
        "rfc_notes": "Multiple PATCH operations in a single request (RFC 7644 §3.5.2)",
        "payload": {
            "schemas": ["urn:ietf:params:scim:api:messages:2.0:PatchOp"],
            "Operations": [
                {
                    "op": "add",
                    "path": "emails",
                    "value": [{"value": "new@example.com", "type": "work"}],
                },
                {
                    "op": "replace",
                    "path": "displayName",
                    "value": "New Display Name",
                },
                {
                    "op": "remove",
                    "path": "phoneNumbers",
                },
            ],
        },
    },
    # ------------------------------------------------------------------
    # Invalid examples (educational)
    # ------------------------------------------------------------------
    {
        "id": "invalid-missing-schemas",
        "name": "Missing schemas (invalid)",
        "description": (
            "Payload with no schemas array. Demonstrates the most fundamental "
            "SCIM requirement — every resource must declare its type."
        ),
        "resource_type": "User",
        "operation": "full",
        "valid": False,
        "rfc_notes": "schemas is required on every SCIM resource (RFC 7643 §3.1)",
        "payload": {
            "userName": "alice@example.com",
        },
        "expected_errors": ["Missing required field: 'schemas'"],
    },
    {
        "id": "invalid-missing-username",
        "name": "Missing userName (invalid)",
        "description": (
            "User with schemas but no userName. Shows required attribute checking — "
            "userName is the only required attribute on the User schema."
        ),
        "resource_type": "User",
        "operation": "full",
        "valid": False,
        "rfc_notes": "userName is REQUIRED on User resources (RFC 7643 §4.1)",
        "payload": {
            "schemas": ["urn:ietf:params:scim:schemas:core:2.0:User"],
        },
        "expected_errors": ["User resource missing required attribute: 'userName'"],
    },
    {
        "id": "invalid-client-sets-id",
        "name": "Client sets id (invalid)",
        "description": (
            "User with id set by the client. The id attribute is readOnly — "
            "it is assigned by the server on creation and must not be sent by clients."
        ),
        "resource_type": "User",
        "operation": "full",
        "valid": False,
        "rfc_notes": "id is readOnly — assigned by server, not client (RFC 7643 §3.1)",
        "payload": {
            "schemas": ["urn:ietf:params:scim:schemas:core:2.0:User"],
            "userName": "alice@example.com",
            "id": "abc123-client-assigned",
        },
        "expected_errors": ["Immutable attribute 'id' should not be set by client"],
    },
    {
        "id": "invalid-null-value",
        "name": "Null attribute value (invalid)",
        "description": (
            "User with displayName set to null. SCIM uses omission to clear "
            "attributes — null values are not permitted. Use PATCH remove instead."
        ),
        "resource_type": "User",
        "operation": "full",
        "valid": False,
        "rfc_notes": "Omit attributes to clear them; null is not valid (RFC 7643 §2.5)",
        "payload": {
            "schemas": ["urn:ietf:params:scim:schemas:core:2.0:User"],
            "userName": "alice@example.com",
            "displayName": None,
        },
        "expected_errors": ["has null value"],
    },
    {
        "id": "invalid-patch-no-op",
        "name": "PATCH missing op (invalid)",
        "description": (
            "PATCH operation object missing the required op field. "
            "Every PATCH operation must specify op (add, remove, or replace)."
        ),
        "resource_type": "PATCH",
        "operation": "patch",
        "valid": False,
        "rfc_notes": "op is required in every PATCH operation object (RFC 7644 §3.5.2)",
        "payload": {
            "schemas": ["urn:ietf:params:scim:api:messages:2.0:PatchOp"],
            "Operations": [
                {"path": "displayName", "value": "No Op Field"},
            ],
        },
        "expected_errors": ["missing required field 'op'"],
    },
    {
        "id": "invalid-patch-bad-op",
        "name": "PATCH invalid op value (invalid)",
        "description": (
            "PATCH operation with op='update', which is not a valid SCIM op. "
            "Only add, remove, and replace are permitted."
        ),
        "resource_type": "PATCH",
        "operation": "patch",
        "valid": False,
        "rfc_notes": "Valid op values are add, remove, replace (RFC 7644 §3.5.2)",
        "payload": {
            "schemas": ["urn:ietf:params:scim:api:messages:2.0:PatchOp"],
            "Operations": [
                {"op": "update", "path": "displayName", "value": "Bad Op"},
            ],
        },
        "expected_errors": ["invalid 'op' value 'update'"],
    },
]

# Public fields returned by the API (expected_errors is internal/test-only)
_PUBLIC_FIELDS = {
    "id", "name", "description", "resource_type",
    "operation", "valid", "rfc_notes", "payload",
}


def get_public_examples() -> List[Dict[str, Any]]:
    """Return examples with only the API-public fields."""
    return [{k: v for k, v in e.items() if k in _PUBLIC_FIELDS} for e in EXAMPLES]
