# Google Workspace Integration Guide

Google Workspace participates in SCIM provisioning primarily as a **SCIM server** — an external identity provider (such as Entra ID or Okta) provisions users inbound to Google Workspace via the [Cloud Identity SCIM API](https://cloud.google.com/identity/docs/how-to/scim-api).

scim-sanity can probe your SCIM server for RFC 7643/7644 conformance and lint payloads your provisioning pipeline sends to Google.

> **Note:** Google Workspace's SCIM client behavior (outbound provisioning to third-party apps) has not been independently verified against this tool. This guide will be expanded with vendor-specific details after further research.

## Prerequisites

- scim-sanity installed (`pip install scim-sanity`)
- A SCIM 2.0 endpoint in scope
- A bearer token for that endpoint

## Server Conformance Probe

If you expose a SCIM server that Google (or any IdP) provisions to, point the probe at it:

```bash
scim-sanity probe https://your-app.example.com/scim/v2 \
    --token $APP_SCIM_TOKEN \
    --i-accept-side-effects
```

The probe runs CRUD lifecycle tests and reports RFC 7643/7644 conformance issues. When failures are present, a prioritised Fix Summary explains what to fix and why.

```bash
# Compat mode — known real-world deviations become warnings instead of failures
scim-sanity probe <url> --token <token> --compat --i-accept-side-effects

# JSON output for CI/CD pipelines
scim-sanity probe <url> --token <token> --json-output --i-accept-side-effects
```

See the main [README](../../README.md) for full probe options.

## Provisioning to Google (Google as SCIM server)

If you are provisioning users *into* Google Workspace from an external IdP via the Cloud Identity SCIM API, the expected payload follows the core User schema. Google's SCIM server uses `externalId` to correlate external directory entries with Google accounts. Consult the [Cloud Identity SCIM API documentation](https://cloud.google.com/identity/docs/how-to/scim-api) for the current attribute mapping reference, as Google's accepted attributes and extension support evolve independently of the core RFC.

## Payload Linting

Use the scim-sanity linter to validate SCIM payloads statically — useful for verifying what your provisioning pipeline generates before it reaches Google:

```bash
# Validate a user payload file
scim-sanity user-payload.json

# Validate a PATCH operation
scim-sanity --patch patch-payload.json

# Validate from stdin
echo '{"schemas":["urn:ietf:params:scim:schemas:core:2.0:User"],"userName":"user@example.com"}' | scim-sanity --stdin
```

## References

- [Google Cloud Identity SCIM API](https://cloud.google.com/identity/docs/how-to/scim-api)
- [Google Workspace Admin SDK — Manage Users](https://developers.google.com/admin-sdk/directory/v1/guides/manage-users)
- [RFC 7643 - SCIM Core Schema](https://tools.ietf.org/html/rfc7643)
- [RFC 7644 - SCIM Protocol](https://tools.ietf.org/html/rfc7644)
