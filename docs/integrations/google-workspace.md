# Google Workspace Integration Guide

Google Workspace can participate in SCIM provisioning in two directions depending on your architecture:

- **Google as SCIM client** — Google Workspace provisions users outbound to your application's SCIM server endpoint (e.g., via a marketplace integration or partner connector).
- **Google as SCIM server** — An external identity provider (such as Entra ID or Okta) provisions users inbound to Google Workspace via the [Cloud Identity SCIM API](https://cloud.google.com/identity/docs/how-to/scim-api).

scim-sanity is relevant to both: probe your SCIM server to verify it's ready to receive from Google, or lint payloads your provisioning pipeline sends to Google.

## Prerequisites

- scim-sanity installed (`pip install scim-sanity`)
- A SCIM 2.0 endpoint in scope (your application server, or Google Cloud Identity SCIM)
- A bearer token for that endpoint

## Server Conformance Probe

If Google Workspace is provisioning to your application, point the probe at your app's SCIM server — the endpoint Google will connect to:

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

## What Google Sends

### User provisioning (Google as SCIM client)

When Google Workspace provisions users to a third-party application, it sends core User attributes. Google does not use the Enterprise User extension in the same way Entra ID does — payloads are generally leaner:

```json
{
  "schemas": ["urn:ietf:params:scim:schemas:core:2.0:User"],
  "userName": "john.doe@example.com",
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
  "active": true
}
```

**Key points:**

- `userName` is the user's primary Google Workspace email address.
- Your server must return an `id` value on 201 Created. Google stores it and uses it for all subsequent operations on that user.
- Google typically issues a filter lookup before creating a user to check whether they already exist: `GET /Users?filter=userName eq "john.doe@example.com"`.
- The specific attributes sent vary by integration type and attribute mapping configuration. Confirm the exact mapping in your connector configuration.

### Deprovisioning

As with most SCIM clients, Google deprovisions in two steps:

1. **Soft disable** — PATCH to set `active: false`
2. **Hard delete** — DELETE when the user is removed from scope

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

### Provisioning to Google (Google as SCIM server)

If you are provisioning users *into* Google Workspace from an external IdP via the Cloud Identity SCIM API, the expected payload follows the core User schema. Google's SCIM server uses `externalId` to correlate external directory entries with Google accounts. Consult the [Cloud Identity SCIM API documentation](https://cloud.google.com/identity/docs/how-to/scim-api) for the current attribute mapping reference, as Google's accepted attributes and extension support evolve independently of the core RFC.

## Payload Linting

Use the scim-sanity linter to validate SCIM payloads statically — useful for verifying what your provisioning pipeline generates before it reaches Google, or for understanding what your SCIM server should expect from Google:

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

Correct SCIM implementation supports identity governance good practices: accounts are provisioned and deprovisioned through a controlled, auditable pipeline; attributes are validated before reaching your directory; and provisioning events can be logged and correlated across systems.

For formal compliance mapping to CIS Google Workspace Benchmark controls or other frameworks, consult your organisation's compliance team with the specific controls in scope.

## References

- [Google Cloud Identity SCIM API](https://cloud.google.com/identity/docs/how-to/scim-api)
- [Google Workspace Admin SDK — Manage Users](https://developers.google.com/admin-sdk/directory/v1/guides/manage-users)
- [CIS Google Workspace Benchmark](https://downloads.cisecurity.org/#/)
- [RFC 7643 - SCIM Core Schema](https://tools.ietf.org/html/rfc7643)
- [RFC 7644 - SCIM Protocol](https://tools.ietf.org/html/rfc7644)
