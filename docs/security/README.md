# Security and Compliance Documentation

This directory contains documentation on how scim-sanity supports security and compliance requirements.

## Contents

- **[Compliance Guide](./compliance.md)** - How scim-sanity supports CIS and Microsoft Security Benchmark compliance

## Overview

scim-sanity helps ensure compliance with security frameworks by validating SCIM payloads before they're sent to identity providers. This prevents:

- Invalid configurations that could bypass security controls
- Missing required security attributes
- Improper role assignments
- Security policy violations

## Supported Frameworks

### CIS Benchmarks
- CIS Microsoft Azure Foundations Benchmark
- CIS Google Workspace Benchmark

### Microsoft Security Benchmarks
- Microsoft Cloud Security Benchmark
- Identity Management (IM-*) controls
- Privileged Access (PA-*) controls

## Key Benefits

1. **Pre-provisioning validation**: Catch security issues before they reach identity providers
2. **Automated compliance**: Integrate validation into CI/CD pipelines
3. **Audit support**: Validate payloads as part of compliance audits
4. **Security best practices**: Ensure SCIM payloads follow security requirements

## See Also

- [Main Documentation](../README.md)
- [Integration Guides](../integrations/)
- [Ansible Integration](../ansible/README.md)

