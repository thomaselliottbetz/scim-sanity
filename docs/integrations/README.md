# Identity Provider Integration Guides

This directory contains integration guides for using scim-sanity with various identity providers. Each guide covers payload validation (linting) and server conformance probing for User, Group, Agent, and AgenticApplication resource types.

## Available Guides

- **[Microsoft Entra ID Integration](./entra-id.md)** - Validate SCIM payloads for Entra ID provisioning
- **[Google Workspace Integration](./google-workspace.md)** - Validate SCIM payloads for Google Workspace provisioning

## Common Patterns

### Pre-Provisioning Validation

All integration guides demonstrate the same core pattern:

1. **Validate** SCIM payloads with scim-sanity
2. **Provision** only if validation passes
3. **Handle errors** gracefully

### CI/CD Integration

Each guide includes examples for:
- GitHub Actions workflows
- Shell-based validation-and-provision scripts

### Security and Compliance

All guides reference:
- CIS Benchmark controls
- Security best practices
- Compliance requirements
- Common mistakes and how to avoid them

## Getting Started

1. Choose your identity provider guide
2. Review the common SCIM operations
3. Follow the validation workflow examples
4. Integrate into your provisioning pipeline

## See Also

- [Main scim-sanity Documentation](../../README.md)
- [Ansible Integration](../../ansible/README.md)
- [Security and Compliance Documentation](../security/compliance.md)

