# Security and Compliance with scim-sanity

This guide demonstrates how scim-sanity supports compliance with security frameworks and benchmarks, including CIS Benchmarks and Microsoft Security Benchmarks.

## Overview

Validating SCIM payloads before provisioning to identity providers helps ensure compliance with security standards by:

- Ensuring required security attributes are present
- Preventing invalid configurations that could bypass security controls
- Validating role assignments follow least privilege principles
- Supporting audit and compliance workflows

## CIS Benchmark Compliance

### CIS Microsoft Azure Foundations Benchmark

scim-sanity supports compliance with the [CIS Microsoft Azure Foundations Benchmark v5.0.0](https://downloads.cisecurity.org/#/), particularly Section 5: Identity Services.

#### Section 5.3: Periodic Identity Reviews

**Control 5.3.2: Ensure that guest users are reviewed on a regular basis**

SCIM validation ensures guest user provisioning payloads are properly structured:

```bash
# Validate guest user payload before provisioning
scim-sanity guest-user-payload.json
```

**How scim-sanity supports this control:**
- Validates guest user SCIM payloads contain required attributes
- Ensures proper user type classification
- Prevents invalid guest user configurations

**Control 5.3.4: Ensure that all 'privileged' role assignments are periodically reviewed**

SCIM validation ensures role assignment payloads are valid:

```bash
# Validate role assignment PATCH operation
scim-sanity --patch role-assignment-patch.json
```

**How scim-sanity supports this control:**
- Validates PATCH operations for role assignments
- Ensures proper role assignment structure
- Prevents invalid role modifications

**Control 5.3.5: Ensure disabled user accounts do not have read, write, or owner permissions**

SCIM validation ensures account status changes are properly structured:

```bash
# Validate account deactivation payload
scim-sanity --patch deactivate-user-patch.json
```

**How scim-sanity supports this control:**
- Validates account status change operations
- Ensures proper PATCH structure for deactivation
- Prevents invalid status modifications

#### Section 5.1 & 5.2: Security Defaults and Conditional Access

**Control 5.1.2 / 5.2.4: Ensure multifactor authentication is enabled**

SCIM validation ensures user provisioning payloads are structured correctly for MFA requirements:

```bash
# Validate user payload before provisioning (MFA will be enforced by Entra ID)
scim-sanity user-payload.json
```

**How scim-sanity supports this control:**
- Validates user provisioning payloads are correct
- Ensures users are provisioned with proper attributes
- Prevents provisioning errors that could bypass MFA requirements

### CIS Google Workspace Benchmark

scim-sanity supports compliance with the [CIS Google Workspace Benchmark](https://downloads.cisecurity.org/#/), particularly Section 1: Directory and Section 4: Security.

#### Section 1.1: Users

**Control 1.1.1-1.1.3: Super Admin account management**

SCIM validation ensures admin user provisioning follows security requirements:

```bash
# Validate admin user payload
scim-sanity admin-user-payload.json
```

**How scim-sanity supports this control:**
- Validates admin user provisioning payloads
- Ensures proper user account structure
- Prevents invalid admin account configurations

#### Section 4.1: Authentication

**Control 4.1.1.1: Ensure 2-Step Verification is enforced for all users in administrative roles**

SCIM validation ensures users are provisioned correctly for 2SV requirements:

```bash
# Validate user payload for admin role
scim-sanity admin-user-payload.json
```

**How scim-sanity supports this control:**
- Validates user provisioning payloads are structured correctly
- Ensures users can be properly enrolled in 2SV
- Prevents provisioning errors

#### Section 4.2.1: API Controls

**Control 4.2.1.3: Ensure internal apps can access Google Workspace APIs**

SCIM validation ensures SCIM API usage is properly structured:

```bash
# Validate SCIM payload before API call
scim-sanity user-payload.json && \
  curl -X POST "$GOOGLE_SCIM_ENDPOINT/Users" \
    -H "Authorization: Bearer $TOKEN" \
    -d @user-payload.json
```

**How scim-sanity supports this control:**
- Validates SCIM API payloads before sending
- Ensures proper API usage structure
- Prevents invalid API calls

## Microsoft Security Benchmark Compliance

scim-sanity supports compliance with the [Microsoft Cloud Security Benchmark](https://github.com/MicrosoftDocs/SecurityBenchmarks), particularly Identity Management controls.

### Identity Management (IM-*) Controls

**IM-1: Use centralized identity and authentication system**

SCIM validation ensures centralized identity provisioning:

```bash
# Validate user payload for centralized provisioning
scim-sanity user-payload.json
```

**How scim-sanity supports this control:**
- Validates SCIM payloads used for centralized identity provisioning
- Ensures proper user account structure
- Prevents local account creation by validating centralized provisioning

**IM-3: Manage application identities securely and automatically**

SCIM validation ensures application identity provisioning is correct:

```bash
# Validate service principal or managed identity provisioning
scim-sanity app-identity-payload.json
```

**How scim-sanity supports this control:**
- Validates application identity provisioning payloads
- Ensures proper service principal structure
- Supports automated identity management workflows

**IM-7: Restrict resource access based on conditions**

SCIM validation ensures conditional access policies are properly applied:

```bash
# Validate user payload (conditional access applied by Entra ID)
scim-sanity user-payload.json
```

**How scim-sanity supports this control:**
- Validates user provisioning payloads are correct
- Ensures users can be properly subject to conditional access policies
- Prevents provisioning errors that could bypass conditional access

**IM-8: Restrict the exposure of credential and secrets**

SCIM validation ensures credential management is secure:

```bash
# Validate user payload (credentials managed securely)
scim-sanity user-payload.json
```

**How scim-sanity supports this control:**
- Validates user provisioning payloads don't expose credentials
- Ensures proper credential management structure
- Prevents insecure credential handling

### Privileged Access (PA-*) Controls

**PA-7: Follow just enough administration (least privilege) principle**

SCIM validation ensures role assignments follow least privilege:

```bash
# Validate role assignment PATCH operation
scim-sanity --patch role-assignment-patch.json
```

**How scim-sanity supports this control:**
- Validates role assignment operations
- Ensures proper RBAC structure
- Prevents invalid role assignments that could violate least privilege

## Compliance Validation Workflows

### Pre-Provisioning Validation

Always validate SCIM payloads before provisioning to ensure compliance:

```bash
#!/usr/bin/env bash
# compliance-validation.sh

PAYLOAD_FILE="$1"

# Validate payload
if scim-sanity "$PAYLOAD_FILE"; then
    echo "✅ SCIM payload validated - compliant with security requirements"
    # Proceed with provisioning
else
    echo "❌ SCIM payload validation failed - not compliant"
    exit 1
fi
```

### CI/CD Compliance Checks

Integrate validation into CI/CD pipelines for automated compliance:

```yaml
# .github/workflows/compliance-check.yml
name: SCIM Compliance Validation

on:
  pull_request:
    paths:
      - 'scim-payloads/**'

jobs:
  validate-compliance:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v3
      
      - name: Install scim-sanity
        run: pip install scim-sanity
      
      - name: Validate all SCIM payloads
        run: |
          for file in scim-payloads/**/*.json; do
            echo "Validating $file..."
            scim-sanity "$file" || exit 1
          done
      
      - name: Compliance check passed
        run: echo "✅ All SCIM payloads comply with security requirements"
```

### Audit Workflow

Validate SCIM payloads as part of compliance audits:

```bash
#!/usr/bin/env bash
# audit-validation.sh

# Validate all SCIM payloads in repository
find . -name "*.json" -path "*/scim-payloads/*" | while read file; do
    echo "Auditing: $file"
    if scim-sanity "$file"; then
        echo "  ✅ Compliant"
    else
        echo "  ❌ Non-compliant"
        scim-sanity "$file"  # Show errors
    fi
done
```

## Compliance Reporting

### Generate Compliance Report

```bash
#!/usr/bin/env bash
# compliance-report.sh

REPORT_FILE="compliance-report.txt"

echo "SCIM Compliance Report - $(date)" > "$REPORT_FILE"
echo "=================================" >> "$REPORT_FILE"
echo "" >> "$REPORT_FILE"

find . -name "*.json" -path "*/scim-payloads/*" | while read file; do
    echo "Validating: $file" >> "$REPORT_FILE"
    if scim-sanity "$file" >> "$REPORT_FILE" 2>&1; then
        echo "  Status: COMPLIANT" >> "$REPORT_FILE"
    else
        echo "  Status: NON-COMPLIANT" >> "$REPORT_FILE"
    fi
    echo "" >> "$REPORT_FILE"
done

cat "$REPORT_FILE"
```

## Best Practices for Compliance

1. **Validate before provisioning**: Always validate SCIM payloads before sending to identity providers
2. **Automate validation**: Integrate validation into CI/CD pipelines
3. **Document exceptions**: If validation fails, document why and get approval
4. **Regular audits**: Periodically validate all SCIM payloads in your repository
5. **Version control**: Store validated SCIM payloads in version control for audit trails

## References

### CIS Benchmarks
- [CIS Microsoft Azure Foundations Benchmark v5.0.0](https://downloads.cisecurity.org/#/)
- [CIS Google Workspace Benchmark](https://downloads.cisecurity.org/#/)

### Microsoft Security Benchmarks
- [Microsoft Cloud Security Benchmark](https://github.com/MicrosoftDocs/SecurityBenchmarks)
- [Microsoft Security Benchmarks Documentation](https://docs.microsoft.com/azure/security/benchmarks/)

### Related Documentation
- [Entra ID Integration Guide](../integrations/entra-id.md)
- [Google Workspace Integration Guide](../integrations/google-workspace.md)
- [Ansible Integration](../ansible/README.md)

