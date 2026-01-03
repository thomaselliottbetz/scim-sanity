# Microsoft Entra ID Integration Guide

This guide demonstrates how to use scim-sanity to validate SCIM payloads before provisioning users and groups to Microsoft Entra ID (formerly Azure Active Directory).

## Overview

Microsoft Entra ID uses SCIM 2.0 for automated user and group provisioning. Validating SCIM payloads with scim-sanity before sending them to Entra ID helps ensure:

- Required attributes are present
- Immutable attributes aren't modified
- Payloads conform to SCIM 2.0 standards
- Security and compliance requirements are met

## Prerequisites

- scim-sanity installed (`pip install scim-sanity`)
- Access to Microsoft Entra ID with SCIM provisioning configured
- SCIM endpoint URL and authentication token

## Common SCIM Operations

### Creating Users

Entra ID expects SCIM User resources with specific required attributes:

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

Always validate SCIM payloads before sending them to Entra ID:

```bash
#!/usr/bin/env bash
# validate-and-provision.sh

PAYLOAD_FILE="user-payload.json"
SCIM_ENDPOINT="https://graph.microsoft.com/v2/servicePrincipals/{id}/synchronization/jobs/{jobId}/schema"

# Validate payload
if scim-sanity "$PAYLOAD_FILE"; then
    echo "✅ Validation passed, provisioning user..."
    curl -X POST "$SCIM_ENDPOINT/Users" \
        -H "Authorization: Bearer $ENTRA_TOKEN" \
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
name: Provision Users to Entra ID

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
      
      - name: Provision to Entra ID
        if: success()
        run: |
          curl -X POST "${{ secrets.ENTRA_SCIM_ENDPOINT }}/Users" \
            -H "Authorization: Bearer ${{ secrets.ENTRA_TOKEN }}" \
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

- **CIS Azure Foundations 5.3.2**: Guest user reviews - Validate guest user provisioning payloads
- **CIS Azure Foundations 5.3.4**: Privileged role reviews - Validate role assignment payloads
- **CIS Azure Foundations 5.3.5**: Disabled accounts - Validate account status changes

### Microsoft Security Benchmarks

SCIM validation supports:

- **IM-1**: Centralized identity and authentication system
- **IM-3**: Manage application identities securely and automatically
- **PA-7**: Follow just enough administration (least privilege) principle

## Example: Complete User Provisioning Workflow

```bash
#!/usr/bin/env bash
set -e

USER_FILE="new-user.json"
SCIM_ENDPOINT="${ENTRA_SCIM_ENDPOINT}/Users"

# Step 1: Validate payload
echo "Validating SCIM payload..."
if ! scim-sanity "$USER_FILE"; then
    echo "Validation failed. Fix errors and try again."
    exit 1
fi

# Step 2: Provision user
echo "Provisioning user to Entra ID..."
RESPONSE=$(curl -s -w "\n%{http_code}" -X POST "$SCIM_ENDPOINT" \
    -H "Authorization: Bearer $ENTRA_TOKEN" \
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

See the [Ansible Integration Guide](../ansible/README.md) for using scim-sanity validation in Ansible playbooks with Entra ID.

## References

- [Microsoft Entra ID SCIM Documentation](https://learn.microsoft.com/entra/identity/app-provisioning/use-scim-to-provision-users-and-groups)
- [SCIM 2.0 Protocol Reference](https://learn.microsoft.com/entra/identity/app-provisioning/use-scim-to-provision-users-and-groups#scim-protocol-reference)
- [CIS Azure Foundations Benchmark](https://downloads.cisecurity.org/#/)
- [Microsoft Cloud Security Benchmark](https://learn.microsoft.com/azure/security/benchmarks/)

