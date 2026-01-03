# Google Workspace Integration Guide

This guide demonstrates how to use scim-sanity to validate SCIM payloads before provisioning users and groups to Google Workspace.

## Overview

Google Workspace uses SCIM 2.0 for automated user and group provisioning. Validating SCIM payloads with scim-sanity before sending them to Google Workspace helps ensure:

- Required attributes are present
- Immutable attributes aren't modified
- Payloads conform to SCIM 2.0 standards
- Security and compliance requirements are met

## Prerequisites

- scim-sanity installed (`pip install scim-sanity`)
- Google Workspace with SCIM provisioning configured
- SCIM endpoint URL and OAuth 2.0 authentication token

## Common SCIM Operations

### Creating Users

Google Workspace expects SCIM User resources with specific required attributes:

```json
{
  "schemas": ["urn:ietf:params:scim:schemas:core:2.0:User"],
  "userName": "john.doe@example.com",
  "name": {
    "givenName": "John",
    "familyName": "Doe"
  },
  "emails": [
    {
      "value": "john.doe@example.com",
      "type": "work",
      "primary": true
    }
  ],
  "active": true
}
```

**Validate before sending:**

```bash
# Save payload to file
cat > user-payload.json << 'EOF'
{
  "schemas": ["urn:ietf:params:scim:schemas:core:2.0:User"],
  "userName": "john.doe@example.com",
  "name": {
    "givenName": "John",
    "familyName": "Doe"
  },
  "emails": [
    {
      "value": "john.doe@example.com",
      "type": "work",
      "primary": true
    }
  ],
  "active": true
}
EOF

# Validate
scim-sanity user-payload.json
```

### Creating Groups

```json
{
  "schemas": ["urn:ietf:params:scim:schemas:core:2.0:Group"],
  "displayName": "Engineering Team",
  "members": [
    {
      "value": "user-id-123",
      "display": "John Doe",
      "type": "User"
    }
  ]
}
```

### Updating Users (PATCH)

```json
{
  "schemas": ["urn:ietf:params:scim:api:messages:2.0:PatchOp"],
  "Operations": [
    {
      "op": "replace",
      "path": "active",
      "value": false
    }
  ]
}
```

**Validate PATCH operations:**

```bash
scim-sanity --patch patch-payload.json
```

## Validation Workflow

### Pre-Provisioning Validation

Always validate SCIM payloads before sending them to Google Workspace:

```bash
#!/usr/bin/env bash
# validate-and-provision.sh

PAYLOAD_FILE="user-payload.json"
SCIM_ENDPOINT="https://www.googleapis.com/scim/v1/Users"

# Validate payload
if scim-sanity "$PAYLOAD_FILE"; then
    echo "✅ Validation passed, provisioning user..."
    curl -X POST "$SCIM_ENDPOINT" \
        -H "Authorization: Bearer $GOOGLE_TOKEN" \
        -H "Content-Type: application/scim+json" \
        -d @"$PAYLOAD_FILE"
else
    echo "❌ Validation failed, not provisioning"
    exit 1
fi
```

### CI/CD Integration

Validate SCIM payloads in your CI/CD pipeline:

```yaml
# .github/workflows/provision-users.yml
name: Provision Users to Google Workspace

on:
  workflow_dispatch:
    inputs:
      user_file:
        description: 'Path to user payload file'
        required: true

jobs:
  validate-and-provision:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v3
      
      - name: Install scim-sanity
        run: pip install scim-sanity
      
      - name: Validate SCIM payload
        run: scim-sanity ${{ github.event.inputs.user_file }}
      
      - name: Provision to Google Workspace
        if: success()
        run: |
          curl -X POST "${{ secrets.GOOGLE_SCIM_ENDPOINT }}/Users" \
            -H "Authorization: Bearer ${{ secrets.GOOGLE_TOKEN }}" \
            -H "Content-Type: application/scim+json" \
            -d @${{ github.event.inputs.user_file }}
```

## Common Mistakes and How scim-sanity Catches Them

### Missing Required Attributes

**Invalid payload:**
```json
{
  "schemas": ["urn:ietf:params:scim:schemas:core:2.0:User"]
  // Missing userName - will fail validation
}
```

**scim-sanity error:**
```
❌ Missing required attribute: 'userName' (schema: urn:ietf:params:scim:schemas:core:2.0:User)
```

### Setting Immutable Attributes

**Invalid payload:**
```json
{
  "schemas": ["urn:ietf:params:scim:schemas:core:2.0:User"],
  "userName": "user@example.com",
  "id": "12345"  // ❌ Cannot set id - it's read-only
}
```

**scim-sanity error:**
```
❌ Immutable attribute 'id' should not be set by client (mutability: readOnly)
```

### Using Null Values

**Invalid payload:**
```json
{
  "schemas": ["urn:ietf:params:scim:schemas:core:2.0:User"],
  "userName": "user@example.com",
  "displayName": null  // ❌ Use PATCH remove instead
}
```

**scim-sanity error:**
```
❌ Attribute 'displayName' has null value. Use PATCH 'remove' operation to clear attributes instead
```

## Security Considerations

### Compliance with CIS Controls

Validating SCIM payloads supports compliance with:

- **CIS Google Workspace 1.1.1-1.1.3**: Super Admin account management - Validate admin user provisioning
- **CIS Google Workspace 4.1.1**: 2-Step Verification enforcement - Validate user provisioning with MFA requirements
- **CIS Google Workspace 4.2.1**: API Controls - Validate SCIM API usage and application identities

### Google Workspace Security Best Practices

SCIM validation supports:

- **Section 1.1 (Users)**: Proper user account creation and management
- **Section 4.1 (Authentication)**: Secure user provisioning with authentication requirements
- **Section 4.2.1 (API Controls)**: Secure SCIM API usage for provisioning

## Example: Complete User Provisioning Workflow

```bash
#!/usr/bin/env bash
set -e

USER_FILE="new-user.json"
SCIM_ENDPOINT="${GOOGLE_SCIM_ENDPOINT}/Users"

# Step 1: Validate payload
echo "Validating SCIM payload..."
if ! scim-sanity "$USER_FILE"; then
    echo "Validation failed. Fix errors and try again."
    exit 1
fi

# Step 2: Provision user
echo "Provisioning user to Google Workspace..."
RESPONSE=$(curl -s -w "\n%{http_code}" -X POST "$SCIM_ENDPOINT" \
    -H "Authorization: Bearer $GOOGLE_TOKEN" \
    -H "Content-Type: application/scim+json" \
    -d @"$USER_FILE")

HTTP_CODE=$(echo "$RESPONSE" | tail -n1)
BODY=$(echo "$RESPONSE" | sed '$d')

if [ "$HTTP_CODE" -eq 201 ]; then
    echo "✅ User provisioned successfully"
    echo "$BODY" | jq '.id'
else
    echo "❌ Provisioning failed (HTTP $HTTP_CODE)"
    echo "$BODY"
    exit 1
fi
```

## Using with Ansible

See the [Ansible Integration Guide](../ansible/README.md) for using scim-sanity validation in Ansible playbooks with Google Workspace.

## References

- [Google Workspace SCIM API Documentation](https://developers.google.com/admin-sdk/directory/v1/guides/manage-users)
- [Google Workspace Provisioning API](https://developers.google.com/admin-sdk/directory/v1/guides/manage-users)
- [CIS Google Workspace Benchmark](https://downloads.cisecurity.org/#/)
- [SCIM 2.0 Protocol Specification](https://tools.ietf.org/html/rfc7644)

