# Security and Compliance with scim-sanity

scim-sanity contributes to a compliant identity provisioning pipeline in specific, narrow ways. This document describes what the tool actually does and does not do in a compliance context, and provides practical workflows for integrating it into audit and CI/CD processes.

## What scim-sanity Actually Contributes

**Payload structural correctness** — The linter ensures that SCIM resources sent to or received from a SCIM server are well-formed: required attributes are present, read-only attributes are not set by the client, null values are not used where PATCH remove is required, and schema URNs are correct. Structurally malformed provisioning payloads are a common source of silent failures in identity pipelines.

**Deprovisioning correctness** — The linter validates that PATCH operations used to deactivate accounts (`active: false`) are properly structured. A malformed deprovisioning operation that silently fails is a compliance risk.

**Audit trail capability** — The server probe detects whether a SCIM server returns `meta.created` and `meta.lastModified` timestamps. These fields are the foundation of incremental sync and provisioning audit trails. A server that omits them cannot support time-correlated audit logging without additional instrumentation.

**writeOnly attribute enforcement** — The probe detects whether a SCIM server incorrectly returns writeOnly attributes (such as passwords) in responses, which would constitute a credential exposure.

**What scim-sanity does not do** — It does not enforce access control policies, manage role assignments, configure MFA, enforce conditional access, or prevent any action at the identity provider level. Claims beyond structural payload validation and server conformance testing are outside the tool's scope.

---

## CI/CD Integration

Validate SCIM payloads as part of your pipeline to catch structural errors before they reach a SCIM server:

```yaml
# .github/workflows/compliance-check.yml
name: SCIM Payload Validation

on:
  pull_request:
    paths:
      - 'scim-payloads/**'

jobs:
  validate:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4

      - name: Install scim-sanity
        run: pip install scim-sanity

      - name: Validate all SCIM payloads
        run: |
          for file in scim-payloads/**/*.json; do
            echo "Validating $file..."
            scim-sanity "$file" || exit 1
          done
```

## Audit Workflow

Validate all SCIM payloads in a repository as part of a periodic audit:

```bash
#!/usr/bin/env bash
# audit-validation.sh

find . -name "*.json" -path "*/scim-payloads/*" | while read file; do
    echo "Auditing: $file"
    if scim-sanity "$file"; then
        echo "  PASS"
    else
        echo "  FAIL"
    fi
done
```

## Compliance Reporting

Generate a simple validation report across a payload directory:

```bash
#!/usr/bin/env bash
# compliance-report.sh

REPORT_FILE="scim-validation-report-$(date +%Y%m%d).txt"

echo "SCIM Payload Validation Report — $(date)" > "$REPORT_FILE"
echo "==========================================" >> "$REPORT_FILE"

find . -name "*.json" -path "*/scim-payloads/*" | while read file; do
    echo "" >> "$REPORT_FILE"
    echo "File: $file" >> "$REPORT_FILE"
    if scim-sanity "$file" >> "$REPORT_FILE" 2>&1; then
        echo "Status: PASS" >> "$REPORT_FILE"
    else
        echo "Status: FAIL" >> "$REPORT_FILE"
    fi
done

cat "$REPORT_FILE"
```

## Server Conformance and Audit Trails

Run the probe against your SCIM server to verify it supports the fields required for audit logging:

```bash
scim-sanity probe https://your-app.example.com/scim/v2 \
    --token $SCIM_TOKEN \
    --json-output \
    --i-accept-side-effects | jq '.issues'
```

The `issues` array in the JSON output identifies structural gaps — including missing `meta.created`/`meta.lastModified` — that would affect your ability to maintain a complete provisioning audit trail.

## References

- [RFC 7643 - SCIM Core Schema](https://tools.ietf.org/html/rfc7643)
- [RFC 7644 - SCIM Protocol](https://tools.ietf.org/html/rfc7644)
- [CIS Benchmarks](https://downloads.cisecurity.org/#/)
- [Microsoft Cloud Security Benchmark](https://github.com/MicrosoftDocs/SecurityBenchmarks)
- [Entra ID Integration Guide](../integrations/entra-id.md)
- [Google Workspace Integration Guide](../integrations/google-workspace.md)
