# Identity Provider Integration Guides

Integration guides for using scim-sanity with identity providers. Each guide covers the SCIM client/server relationship for that IdP, what the IdP sends in its provisioning payloads, server conformance probing, and payload linting.

## Available Guides

- **[Microsoft Entra ID](./entra-id.md)** — Entra ID acts as a SCIM client, provisioning users to your application's SCIM server. Covers probing your server for Entra ID compatibility, the Enterprise User extension, and the `externalId` correlation pattern.
- **[Google Workspace](./google-workspace.md)** — Google Workspace can act as either a SCIM client (provisioning to your app) or a SCIM server (receiving from an external IdP via Cloud Identity SCIM). Covers both scenarios.

## See Also

- [Main scim-sanity Documentation](../../README.md)
- [Ansible Integration](../../ansible/README.md)
- [Security and Compliance Documentation](../security/compliance.md)
