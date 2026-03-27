# Identity Provider Integration Guides

Integration guides for using scim-sanity with identity providers. Each guide covers the SCIM client/server relationship for that IdP, what the IdP sends in its provisioning payloads, server conformance probing, and payload linting.

## Available Guides

- **[Microsoft Entra ID](./entra-id.md)** — Entra ID acts as a SCIM client, provisioning users to your application's SCIM server. Covers probing your server for Entra ID compatibility, the Enterprise User extension, and the `externalId` correlation pattern.
- **[Google Workspace](./google-workspace.md)** — Google Workspace as a SCIM server receiving inbound provisioning via the Cloud Identity SCIM API. Google's SCIM client behavior has not yet been independently verified.

## See Also

- [Main scim-sanity Documentation](../../README.md)
- [Ansible Integration](../../ansible/README.md)
- [Security and Compliance Documentation](../security/compliance.md)
