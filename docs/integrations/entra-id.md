# Microsoft Entra ID Integration Guide

Microsoft Entra ID acts as a **SCIM client** — it pushes user and group provisioning data to your application's SCIM server endpoint. scim-sanity tests whether your SCIM server is ready to receive it.

This guide covers probing your SCIM server for Entra ID compatibility, understanding what Entra ID sends, and linting payloads with the scim-sanity validator.

## Prerequisites

- scim-sanity installed (`pip install scim-sanity`)
- A SCIM 2.0 server endpoint your application exposes for Entra ID to provision to
- A bearer token for that endpoint

## Server Conformance Probe

Point the probe at your application's SCIM server — the endpoint that Entra ID will connect to:

```bash
scim-sanity probe https://your-app.example.com/scim/v2 \
    --token $APP_SCIM_TOKEN \
    --i-accept-side-effects
```

The probe runs a full 7-phase CRUD lifecycle test and reports RFC 7643/7644 conformance issues. When failures are present, a prioritised Fix Summary explains what to fix and why.

```bash
# Compat mode — known real-world deviations become warnings instead of failures
scim-sanity probe <url> --token <token> --compat --i-accept-side-effects

# JSON output for CI/CD pipelines
scim-sanity probe <url> --token <token> --json-output --i-accept-side-effects
```

See the main [README](../../README.md) for full probe options.

## What Entra ID Sends

Understanding Entra ID's provisioning payloads helps you build a SCIM server that handles them correctly.

### User provisioning

Entra ID provisions users using the core User schema plus the Enterprise User extension:

```json
{
  "schemas": [
    "urn:ietf:params:scim:schemas:core:2.0:User",
    "urn:ietf:params:scim:schemas:extension:enterprise:2.0:User"
  ],
  "userName": "john.doe@example.com",
  "externalId": "entra-object-id-or-guid",
  "name": {
    "givenName": "John",
    "familyName": "Doe"
  },
  "displayName": "John Doe",
  "emails": [
    {
      "value": "john.doe@example.com",
      "type": "work",
      "primary": true
    }
  ],
  "active": true,
  "urn:ietf:params:scim:schemas:extension:enterprise:2.0:User": {
    "department": "Engineering",
    "manager": {
      "value": "manager-scim-id"
    }
  }
}
```

**Key points:**

- `externalId` is the Entra ID object GUID. Your server should store it — Entra uses it as the correlation key to match its records to yours.
- `userName` is typically the UPN (user principal name).
- Not all attributes are sent on every sync cycle. Entra ID sends only changed attributes in delta syncs.
- Your server must return an `id` value on the 201 Created response. Entra ID stores this and uses it for all subsequent operations (GET, PATCH, DELETE) on that user.
- Before creating a user, Entra ID typically issues a filter query to check whether the user already exists: `GET /Users?filter=userName eq "john.doe@example.com"`.

### Group provisioning

```json
{
  "schemas": ["urn:ietf:params:scim:schemas:core:2.0:Group"],
  "displayName": "Engineering Team",
  "externalId": "entra-group-guid",
  "members": [
    {
      "value": "scim-user-id",
      "display": "John Doe"
    }
  ]
}
```

### Deprovisioning

Entra ID deprovisions in two steps:

1. **Soft disable** — PATCH to set `active: false`
2. **Hard delete** — DELETE when the account is fully removed from scope

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

Your server should handle both operations correctly. A server that only implements DELETE and ignores `active` will fail Entra ID's deprovisioning flow.

## Payload Linting

Use the scim-sanity linter to validate SCIM payloads statically before sending them or to understand what your server should expect:

```bash
# Validate a user payload file
scim-sanity user-payload.json

# Validate a PATCH operation
scim-sanity --patch patch-payload.json

# Validate from stdin
echo '{"schemas":["urn:ietf:params:scim:schemas:core:2.0:User"],"userName":"user@example.com"}' | scim-sanity --stdin
```

### Common mistakes the linter catches

**Missing required attributes:**
```json
{
  "schemas": ["urn:ietf:params:scim:schemas:core:2.0:User"]
}
```
```
❌ Missing required attribute: 'userName'
```

**Client setting a read-only attribute:**
```json
{
  "schemas": ["urn:ietf:params:scim:schemas:core:2.0:User"],
  "userName": "user@example.com",
  "id": "12345"
}
```
```
❌ Immutable attribute 'id' should not be set by client (mutability: readOnly)
```

**Null value instead of PATCH remove:**
```json
{
  "schemas": ["urn:ietf:params:scim:schemas:core:2.0:User"],
  "userName": "user@example.com",
  "displayName": null
}
```
```
❌ Attribute 'displayName' has null value. Use PATCH 'remove' operation to clear attributes instead
```

## Security and Compliance

Correct SCIM implementation supports identity governance good practices: accounts are provisioned and deprovisioned through a controlled, auditable pipeline; attributes are validated before reaching your directory; and provisioning events can be correlated against Entra ID's audit logs via `externalId`.

For formal compliance mapping, consult your organisation's compliance team against the specific control frameworks in scope (CIS, MCSB, SOC 2, etc.).

## References

- [Microsoft Entra ID SCIM Documentation](https://learn.microsoft.com/entra/identity/app-provisioning/use-scim-to-provision-users-and-groups)
- [Entra ID SCIM Attribute Mapping Reference](https://learn.microsoft.com/entra/identity/app-provisioning/customize-application-attributes)
- [RFC 7643 - SCIM Core Schema](https://tools.ietf.org/html/rfc7643)
- [RFC 7644 - SCIM Protocol](https://tools.ietf.org/html/rfc7644)
